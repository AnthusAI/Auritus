"""Coqui XTTS-v2 TTS backend (non-commercial, CUDA required)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend


class CoquiBackend(TTSBackend):
    """Generate speech with Coqui XTTS-v2."""

    name = "coqui"
    _model = None

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate 24 kHz mono WAV audio with Coqui XTTS-v2."""
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if CoquiBackend._model is None:
            # TODO: Verify the XTTS-v2 API and speaker configuration.
            from TTS.api import TTS

            CoquiBackend._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        voice = meta.get("voice_id", "Ana Florence")
        audio = CoquiBackend._model.tts(text=text, speaker=voice, language="en")
        samples = audio.tolist() if hasattr(audio, "tolist") else list(audio)
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
