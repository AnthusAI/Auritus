"""Higgs (Boson) TTS backend stub for the local worker.

The production Higgs integration loads model weights at runtime (not baked
into the CLI wheel). See ``docs/TTS_LICENSES.md`` for license and fetch policy.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend


class HiggsBackend(TTSBackend):
    """Higgs TTS backend. Returns a tone WAV until weights are configured."""

    name = "higgs"

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text`` using Higgs when weights are available.

                Until runtime weights are wired, returns a short audible tone WAV
                so the claim-generate-upload-done pipeline can be exercised end to
        end and a listener can hear that audio is playing.

                :param text: TTS input text.
                :param meta: Job metadata (voice_id, name, byline).
                :returns: WAV audio bytes.
        """
        _ = meta
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        return _tone_wav(duration_ms=max(500, min(len(text) * 60, 10000)))


def _tone_wav(
    *, duration_ms: int, sample_rate: int = 22050, frequency: float = 440.0
) -> bytes:
    """Generate a short sine-wave tone as a WAV file.

    :param duration_ms: Duration in milliseconds.
    :param sample_rate: Samples per second.
    :param frequency: Tone frequency in Hz.
    :returns: WAV audio bytes.
    """
    frames = int(sample_rate * (duration_ms / 1000.0))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        samples = []
        for i in range(frames):
            value = int(
                32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            samples.append(struct.pack("<h", value))
        handle.writeframes(b"".join(samples))
    return buffer.getvalue()
