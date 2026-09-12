"""Bark TTS backend (Suno, CUDA required)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend


class BarkBackend(TTSBackend):
    """Generate speech with Suno Bark."""

    name = "bark"
    _processor = None
    _model = None

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate 24 kHz mono WAV audio with Bark."""
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if BarkBackend._processor is None or BarkBackend._model is None:
            # TODO: Verify the Bark Transformers API against the installed release.
            from transformers import AutoProcessor, BarkModel

            BarkBackend._processor = AutoProcessor.from_pretrained("suno/bark")
            BarkBackend._model = BarkModel.from_pretrained("suno/bark")
        inputs = BarkBackend._processor(text, return_tensors="pt")
        audio = BarkBackend._model.generate(**inputs)
        samples = audio.squeeze().tolist()
        return _to_wav(samples, 24000)


def _to_wav(samples: list[Any], sample_rate: int) -> bytes:
    """Convert normalized samples to mono 16-bit WAV bytes."""
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
