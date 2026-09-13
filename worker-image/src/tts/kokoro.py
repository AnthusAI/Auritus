"""Kokoro-82M TTS backend (Apache-2.0, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend


class KokoroBackend(TTSBackend):
    """Kokoro TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/Kokoro-82M-bf16 at runtime via mlx-audio.
    Falls back to PyTorch kokoro on non-Apple platforms.
    """

    name = "kokoro"
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
        """Generate speech audio using Kokoro-82M.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to PyTorch kokoro (slow).

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if KokoroBackend._is_mlx is None:
            KokoroBackend._is_mlx = KokoroBackend._detect_mlx()

        if KokoroBackend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio (Apple Silicon)."""
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if KokoroBackend._model is None:
            KokoroBackend._model = load_model(
                "mlx-community/Kokoro-82M-bf16",
                lazy=False,
            )
        voice = meta.get("voice_id", "af_heart")
        gen = KokoroBackend._model.generate(text, voice=voice)
        result = next(iter(gen))
        audio_np = np.array(result.audio)
        return _to_wav(audio_np, sample_rate=24000)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch kokoro (fallback for non-Apple)."""
        from kokoro import KPipeline

        if KokoroBackend._model is None:
            KokoroBackend._model = KPipeline(lang_code="a")
        voice = meta.get("voice_id", "af_heart")
        results = list(KokoroBackend._model(text, voice=voice))
        audio_tensor = results[0].audio
        audio_list = (
            audio_tensor.tolist()
            if hasattr(audio_tensor, "tolist")
            else list(audio_tensor)
        )
        return _to_wav(audio_list, sample_rate=24000)


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
