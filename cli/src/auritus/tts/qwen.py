"""Qwen3-TTS backend (Apache-2.0, CUDA required)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend


class QwenBackend(TTSBackend):
    """Qwen 3 TTS backend. Loads Qwen3-TTS-0.6B at runtime on GPU."""

    name = "qwen"
    _model = None

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using Qwen3-TTS.

        Loads the model on first call (lazy init, requires CUDA). Returns WAV
        bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if QwenBackend._model is None:
            from qwen_tts import QwenTTS

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


def _to_wav(samples: list[Any], sample_rate: int = 24000) -> bytes:
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
