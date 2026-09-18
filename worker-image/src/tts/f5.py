"""F5-TTS backend (non-autoregressive flow matching, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend

F5_DEFAULT_VOICE = "default"
F5_MLX_MODEL = "mlx-community/F5-TTS"


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

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if F5Backend._is_mlx is None:
            F5Backend._is_mlx = F5Backend._detect_mlx()

        if F5Backend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio (Apple Silicon).

        :param text: TTS input text.
        :param meta: Job metadata.
        :returns: WAV audio bytes.
        """
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if F5Backend._model is None:
            F5Backend._model = load_model(
                F5_MLX_MODEL,
                lazy=False,
            )
        voice = resolve_f5_voice(meta)
        gen = F5Backend._model.generate(text, voice=voice)
        result = next(iter(gen))
        audio_np = np.array(result.audio).reshape(-1)
        return _to_wav(audio_np, sample_rate=24000)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch f5-tts (fallback for non-Apple, e.g. AWS Batch).

        F5TTS's own device default was previously trusted implicitly;
        explicitly resolves and passes cuda/cpu here (mirroring higgs.py,
        chatterbox.py, qwen.py) so a g4dn.xlarge Batch run is verified, not
        assumed, to actually use the GPU it's billed for.

        :param text: TTS input text.
        :param meta: Job metadata.
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
        voice = resolve_f5_voice(meta)
        _ = voice
        ref_file = meta.get("ref_file")
        ref_text = meta.get("ref_text")
        if not ref_file:
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
        infer_kwargs: dict[str, Any] = {"gen_text": text}
        if ref_file:
            infer_kwargs["ref_file"] = ref_file
        if ref_text:
            infer_kwargs["ref_text"] = ref_text
        wav, sr, _ = F5Backend._model.infer(**infer_kwargs)
        audio_np = np.array(wav).reshape(-1)
        return _to_wav(audio_np, sample_rate=int(sr) if sr else 24000)


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
