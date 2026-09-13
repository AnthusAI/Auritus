"""Qwen3-TTS backend (Apache-2.0, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend


class QwenBackend(TTSBackend):
    """Qwen 3 TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit at runtime.
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
                "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit",
                lazy=False,
            )
        voice = meta.get("voice_id", "Chelsie")
        gen = QwenBackend._model.generate(text, voice=voice)
        result = next(iter(gen))
        audio_np = np.array(result.audio)
        return _to_wav(audio_np, sample_rate=24000)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch qwen_tts (fallback for non-Apple)."""
        from qwen_tts import QwenTTS

        if QwenBackend._model is None:
            QwenBackend._model = QwenTTS(
                "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
            )
        voice = meta.get("voice_id", "default")
        audio_tensor = QwenBackend._model.generate(text, voice=voice)
        if isinstance(audio_tensor, tuple):
            audio_tensor = audio_tensor[0]
        if hasattr(audio_tensor, "tolist"):
            samples = audio_tensor.tolist()
        elif hasattr(audio_tensor, "__iter__"):
            samples = list(audio_tensor)
        else:
            samples = [float(audio_tensor)]
        return _to_wav(samples, sample_rate=24000)


def _to_wav(samples: list, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = struct.pack(
            "<" + "h" * len(samples),
            *[
                max(-32768, min(32767, int(float(sample) * 32767)))
                for sample in samples
            ],
        )
        handle.writeframes(frames)
    return buffer.getvalue()
