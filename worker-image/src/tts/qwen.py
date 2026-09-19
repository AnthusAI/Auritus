"""Qwen3-TTS backend (Apache-2.0, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend
from tts.breaks import (
    AURITUS_BREAK_MARKER,
    AURITUS_PAUSE_MARKER,
    DEFAULT_PAUSE_SILENCE_SECONDS,
    parse_voiced_segments,
    split_on_breaks,
    split_on_pauses,
)

__all__ = [
    "AURITUS_BREAK_MARKER",
    "AURITUS_PAUSE_MARKER",
    "QwenBackend",
    "resolve_qwen_voice",
    "parse_voiced_segments",
    "split_on_breaks",
    "split_on_pauses",
]

QWEN_DEFAULT_VOICE = "Ryan"
QWEN_MLX_MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit"
QWEN_TORCH_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
LEGACY_QWEN_VOICES = frozenset({"default", "Chelsie"})

BREAK_SILENCE_SECONDS = 0.4
PAUSE_SILENCE_SECONDS = DEFAULT_PAUSE_SILENCE_SECONDS


def resolve_qwen_voice(meta: dict[str, Any]) -> str:
    """Return a CustomVoice speaker name for Qwen synthesis.

    The Base Qwen checkpoint has no preset voices. Missing, empty, ``default``,
    and the invalid ``Chelsie`` id map to Ryan, an English CustomVoice speaker.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: CustomVoice speaker name.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return QWEN_DEFAULT_VOICE
    if not isinstance(raw, str) or not raw.strip() or raw in LEGACY_QWEN_VOICES:
        return QWEN_DEFAULT_VOICE
    return raw


class QwenBackend(TTSBackend):
    """Qwen 3 TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit at runtime.
    Falls back to PyTorch qwen_tts on non-Apple platforms.
    """

    name = "qwen"
    _model = None
    _is_mlx = None

    @classmethod
    def _detect_mlx(cls) -> bool:
        """Detect whether MLX is available on this platform."""
        import platform

        if platform.system() != "Darwin":
            return False
        machine = platform.machine().lower()
        return machine.startswith(("arm", "aarch"))

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using Qwen3-TTS.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to PyTorch qwen_tts (CUDA).

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if QwenBackend._is_mlx is None:
            QwenBackend._is_mlx = QwenBackend._detect_mlx()

        if QwenBackend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio (Apple Silicon)."""
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if QwenBackend._model is None:
            QwenBackend._model = load_model(
                QWEN_MLX_MODEL,
                lazy=False,
            )
        default_voice = resolve_qwen_voice(meta)
        sample_rate = 24000
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)
        pause_silence = np.zeros(
            int(sample_rate * PAUSE_SILENCE_SECONDS), dtype=np.float32
        )
        all_chunks: list[np.ndarray] = []
        for i, (block_text, block_voice) in enumerate(
            parse_voiced_segments(text, default_voice)
        ):
            if i > 0:
                all_chunks.append(silence)
            pause_segments = split_on_pauses(block_text)
            for p_idx, pause_text in enumerate(pause_segments):
                if p_idx > 0:
                    all_chunks.append(pause_silence)
                gen = QwenBackend._model.generate(pause_text, voice=block_voice)
                for result in gen:
                    all_chunks.append(np.array(result.audio).reshape(-1))
        if not all_chunks:
            raise ValueError("Qwen generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch qwen_tts (fallback for non-Apple)."""
        import numpy as np
        from qwen_tts import Qwen3TTSModel

        if QwenBackend._model is None:
            load_kwargs: dict[str, Any] = {}
            try:
                import torch

                if torch.cuda.is_available():
                    load_kwargs["device_map"] = "cuda:0"
            except ImportError:
                pass
            QwenBackend._model = Qwen3TTSModel.from_pretrained(
                QWEN_TORCH_MODEL,
                **load_kwargs,
            )
        default_voice = resolve_qwen_voice(meta)
        all_samples: list[float] = []
        sample_rate = 24000
        silence = [0.0] * int(sample_rate * BREAK_SILENCE_SECONDS)
        pause_silence = [0.0] * int(sample_rate * PAUSE_SILENCE_SECONDS)
        for i, (block_text, block_voice) in enumerate(
            parse_voiced_segments(text, default_voice)
        ):
            if i > 0:
                all_samples.extend(silence)
            pause_segments = split_on_pauses(block_text)
            for p_idx, pause_text in enumerate(pause_segments):
                if p_idx > 0:
                    all_samples.extend(pause_silence)
                wavs, sr = QwenBackend._model.generate_custom_voice(
                    text=pause_text,
                    speaker=block_voice,
                    language="English",
                )
                sample_rate = int(sr)
                audio_np = np.array(wavs[0]).reshape(-1)
                all_samples.extend(audio_np.tolist())
        if not all_samples:
            raise ValueError("Qwen generated no audio segments")
        return _to_wav(all_samples, sample_rate=sample_rate)


def _to_wav(samples: list, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes."""
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
