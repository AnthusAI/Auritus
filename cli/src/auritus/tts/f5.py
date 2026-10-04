"""F5-TTS backend (non-autoregressive flow matching, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from pathlib import Path
from typing import Any

from auritus.tts.base import BackendUnavailable, TTSBackend
from auritus.tts.breaks import (
    AURITUS_BREAK_MARKER,
    AURITUS_PAUSE_MARKER,
    DEFAULT_PAUSE_SILENCE_SECONDS,
    split_on_breaks,
    split_on_pauses,
)
from auritus.tts.voices import require_reference_audio, resolve_reference_text

__all__ = [
    "AURITUS_BREAK_MARKER",
    "AURITUS_PAUSE_MARKER",
    "F5Backend",
    "resolve_f5_voice",
    "split_on_breaks",
    "split_on_pauses",
]

F5_DEFAULT_VOICE = "default"
#: Voice ids that ask for F5's default voice rather than naming one.
F5_DEFAULT_VOICE_IDS = frozenset({F5_DEFAULT_VOICE})
F5_MLX_MODEL = "mlx-community/F5-TTS"
F5_TORCH_MODEL = "SWivid/F5-TTS"

BREAK_SILENCE_SECONDS = 0.75
PAUSE_SILENCE_SECONDS = DEFAULT_PAUSE_SILENCE_SECONDS


def resolve_f5_voice(meta: dict[str, Any]) -> str:
    """Return an F5 voice or reference style name for synthesis.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Voice identifier string.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return F5_DEFAULT_VOICE
    if isinstance(raw, str) and not raw.strip():
        return F5_DEFAULT_VOICE
    return str(raw)


class F5Backend(TTSBackend):
    """F5-TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/F5-TTS at runtime via mlx-audio or f5-tts-mlx.
    Falls back to PyTorch f5-tts on non-Apple platforms.
    """

    name = "f5"
    _model = None
    _is_mlx = None

    def model_id(self) -> str:
        """:returns: The MLX or PyTorch model repo this machine uses."""
        cls = type(self)
        if cls._is_mlx is None:
            cls._is_mlx = cls._detect_mlx()
        return F5_MLX_MODEL if cls._is_mlx else F5_TORCH_MODEL

    @classmethod
    def _detect_mlx(cls) -> bool:
        """Detect whether MLX is available on this platform.

        :returns: True if running on Apple Silicon Darwin.
        """
        import platform

        if platform.system() != "Darwin":
            return False
        machine = platform.machine().lower()
        return machine.startswith(("arm", "aarch"))

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using F5-TTS.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to PyTorch f5-tts.

        A named voice with no reference recording raises
        :class:`~auritus.tts.voices.VoiceNotFound` before any model loads.

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        :raises VoiceNotFound: If the named voice has no reference recording.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        reference = require_reference_audio(
            resolve_f5_voice(meta),
            meta.get("voices_dir"),
            default_voice_ids=F5_DEFAULT_VOICE_IDS,
        )
        if F5Backend._is_mlx is None:
            F5Backend._is_mlx = F5Backend._detect_mlx()

        if F5Backend._is_mlx:
            return self._generate_mlx(text, meta, reference)
        return self._generate_torch(text, meta, reference)

    def _generate_mlx(
        self, text: str, meta: dict[str, Any], reference: Path | None
    ) -> bytes:
        """Generate via f5-tts-mlx (Apple Silicon).

        :param text: TTS input text.
        :param meta: Job metadata.
        :param reference: The voice's reference recording, or None for a
            default-voice request, which uses f5-tts-mlx's stock reference.
        :returns: WAV audio bytes.
        :raises BackendUnavailable: If a named voice needs f5-tts-mlx and it
            is not installed (the mlx-audio path cannot clone a voice).
        """
        import os
        import re
        import tempfile

        voice = resolve_f5_voice(meta)
        ref_audio = reference
        ref_text = ""
        if reference is not None:
            ref_text = resolve_reference_text(voice, meta.get("voices_dir")) or ""

        try:
            import mlx.core as mx
            import numpy as np
            import soundfile as sf
            from f5_tts_mlx.cfm import F5TTS
            from f5_tts_mlx.generate import (
                TARGET_RMS,
                convert_char_to_pinyin,
                estimated_duration,
            )

            if F5Backend._model is None or not isinstance(F5Backend._model, F5TTS):
                F5Backend._model = F5TTS.from_pretrained("lucasnewman/f5-tts-mlx")

            sample_rate = 24000
            if ref_audio:
                audio_data, file_sr = sf.read(str(ref_audio))
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=1)
                if file_sr != sample_rate:
                    from scipy.signal import resample

                    num_samples = int(len(audio_data) * sample_rate / file_sr)
                    audio_data = resample(audio_data, num_samples)
            else:
                import pkgutil

                ref_bytes = pkgutil.get_data(
                    "f5_tts_mlx", "tests/test_en_1_ref_short.wav"
                )
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as rf:
                    rf.write(ref_bytes)
                    rf_path = rf.name
                try:
                    audio_data, _ = sf.read(rf_path)
                finally:
                    if os.path.exists(rf_path):
                        os.unlink(rf_path)
                ref_text = "Some call me nature, others call me mother nature."

            audio_mx = mx.array(audio_data.astype(np.float32))
            rms = mx.sqrt(mx.mean(mx.square(audio_mx)))
            if rms < TARGET_RMS:
                audio_mx = audio_mx * TARGET_RMS / rms

            blocks = split_on_breaks(text)
            if not blocks:
                blocks = [text]

            frames_per_sec = 24000 / 256
            break_silence = np.zeros(
                int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32
            )
            sentence_silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
            pause_silence = np.zeros(
                int(sample_rate * PAUSE_SILENCE_SECONDS), dtype=np.float32
            )
            all_waves: list[np.ndarray] = []

            for b_idx, block in enumerate(blocks):
                if b_idx > 0:
                    all_waves.append(break_silence)
                sentences = [
                    s.strip() for s in re.split(r"(?<=[.?!])\s+", block) if s.strip()
                ]
                for s_idx, sentence in enumerate(sentences):
                    if s_idx > 0:
                        all_waves.append(sentence_silence)
                    pause_segments = split_on_pauses(sentence)
                    for p_idx, pause_text in enumerate(pause_segments):
                        if p_idx > 0:
                            all_waves.append(pause_silence)
                        dur = int(
                            estimated_duration(audio_mx, ref_text, pause_text, 1.0)
                            * frames_per_sec
                        )
                        pinyin = convert_char_to_pinyin([ref_text + " " + pause_text])
                        wave, _ = F5Backend._model.sample(
                            mx.expand_dims(audio_mx, axis=0),
                            text=pinyin,
                            duration=dur,
                            steps=8,
                        )
                        wave = wave[audio_mx.shape[0] :]
                        mx.eval(wave)
                        all_waves.append(np.array(wave))
                        if hasattr(mx, "clear_cache"):
                            mx.clear_cache()

            if not all_waves:
                raise ValueError("F5-TTS generated no audio")
            combined = np.concatenate(all_waves)
            peak = float(np.max(np.abs(combined)))
            if peak > 0.95:
                combined = combined * (0.95 / peak)
            return _to_wav(combined, sample_rate=sample_rate)
        except ImportError as exc:
            if reference is not None:
                raise BackendUnavailable.from_import_error(self.name, exc) from exc
            import numpy as np
            from mlx_audio.tts.utils import load_model

            if F5Backend._model is None:
                F5Backend._model = load_model(
                    F5_MLX_MODEL,
                    lazy=False,
                )
            gen = F5Backend._model.generate(text, voice=voice)
            result = next(iter(gen))
            audio_np = np.array(result.audio).reshape(-1)
            return _to_wav(audio_np, sample_rate=24000)

    def _generate_torch(
        self, text: str, meta: dict[str, Any], reference: Path | None
    ) -> bytes:
        """Generate via PyTorch f5-tts (fallback for non-Apple, e.g. AWS Batch).

        F5TTS's own device default was previously trusted implicitly;
        explicitly resolves and passes cuda/cpu here (mirroring higgs.py,
        chatterbox.py, qwen.py) so a g4dn.xlarge Batch run is verified, not
        assumed, to actually use the GPU it's billed for.

        :param text: TTS input text.
        :param meta: Job metadata.
        :param reference: The voice's reference recording, or None for a
            default-voice request, which uses the bundled stock reference.
        :returns: WAV audio bytes.
        """
        import os
        import numpy as np
        import torch
        from f5_tts.api import F5TTS

        if F5Backend._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[f5] resolved device={device}", flush=True)
            F5Backend._model = F5TTS(device=device)
        ref_file = None
        ref_text = None
        if reference is not None:
            ref_file = str(reference)
            ref_text = resolve_reference_text(
                resolve_f5_voice(meta), meta.get("voices_dir")
            )
        else:
            local_candidate = os.path.join(
                os.path.dirname(__file__), "basic_ref_en.wav"
            )
            if os.path.exists(local_candidate):
                ref_file = local_candidate
                if not ref_text:
                    ref_text = "Some call me nature, others call me mother nature."
            else:
                try:
                    from importlib.resources import files

                    candidate = str(
                        files("f5_tts").joinpath(
                            "infer/examples/basic/basic_ref_en.wav"
                        )
                    )
                    if os.path.exists(candidate):
                        ref_file = candidate
                        if not ref_text:
                            ref_text = (
                                "Some call me nature, others call me mother nature."
                            )
                except Exception:
                    pass
        blocks = split_on_breaks(text)
        all_waves: list[np.ndarray] = []
        break_silence = np.zeros(int(24000 * BREAK_SILENCE_SECONDS), dtype=np.float32)
        pause_silence = np.zeros(int(24000 * PAUSE_SILENCE_SECONDS), dtype=np.float32)
        out_sr = 24000
        for b_idx, block in enumerate(blocks):
            if b_idx > 0:
                all_waves.append(break_silence)
            pause_segments = split_on_pauses(block)
            for p_idx, pause_text in enumerate(pause_segments):
                if p_idx > 0:
                    all_waves.append(pause_silence)
                infer_kwargs: dict[str, Any] = {"gen_text": pause_text}
                if ref_file:
                    infer_kwargs["ref_file"] = ref_file
                if ref_text:
                    infer_kwargs["ref_text"] = ref_text
                wav, sr, _ = F5Backend._model.infer(**infer_kwargs)
                if sr:
                    out_sr = int(sr)
                all_waves.append(np.array(wav).reshape(-1))
        if not all_waves:
            raise ValueError("F5-TTS generated no audio")
        audio_np = np.concatenate(all_waves) if len(all_waves) > 1 else all_waves[0]
        return _to_wav(audio_np, sample_rate=out_sr)


def _to_wav(samples: list | Any, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes.

    :param samples: Audio amplitude samples.
    :param sample_rate: Audio sampling frequency in Hz.
    :returns: Serialized mono 16-bit WAV bytes.
    """
    buffer = io.BytesIO()
    flat = list(samples)
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = struct.pack(
            "<" + "h" * len(flat),
            *[max(-32768, min(32767, int(float(sample) * 32767))) for sample in flat],
        )
        handle.writeframes(frames)
    return buffer.getvalue()
