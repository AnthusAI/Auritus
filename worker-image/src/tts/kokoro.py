"""Kokoro-82M TTS backend (Apache-2.0 weights, CPU-capable)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend


class KokoroBackend(TTSBackend):
    """Kokoro TTS backend. Loads hexgrad/Kokoro-82M at runtime."""

    name = "kokoro"
    _pipeline = None

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using Kokoro-82M.

        Loads the model on first call (lazy init). Returns WAV bytes at
        24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if KokoroBackend._pipeline is None:
            from kokoro import KPipeline

            KokoroBackend._pipeline = KPipeline(lang_code="a")
        voice = meta.get("voice_id", "af_heart")
        results = list(KokoroBackend._pipeline(text, voice=voice))
        audio_tensor = results[0].audio
        audio_list = (
            audio_tensor.tolist()
            if hasattr(audio_tensor, "tolist")
            else list(audio_tensor)
        )
        return _tensor_to_wav(audio_list, sample_rate=24000)


def _tensor_to_wav(samples: list, sample_rate: int = 24000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = struct.pack(
            "<" + "h" * len(samples),
            *[int(sample * 32767 * 0.95) for sample in samples],
        )
        handle.writeframes(frames)
    return buffer.getvalue()
