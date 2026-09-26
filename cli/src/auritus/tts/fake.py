"""Deterministic, dependency-free backend for specs and demos.

It renders a plain tone whose length follows the text, so hosts can exercise
the whole synthesis path without downloading a model. It is only ever used
when asked for by name; no other backend falls back to it.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend

SAMPLE_RATE = 24000
SECONDS_PER_CHARACTER = 0.02
_VOICE_HZ = {"plain": 220.0, "other": 330.0}


class FakeBackend(TTSBackend):
    """Tone generator standing in for a speech model."""

    name = "fake"
    supports_speed = True

    def model_id(self) -> str:
        """:returns: The fixed identifier ``fake-tone``."""
        return "fake-tone"

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Render a tone lasting ``SECONDS_PER_CHARACTER`` per character.

        :param text: Text to "speak".
        :param meta: ``voice_id`` picks the pitch; ``speed`` shortens it.
        :returns: Mono 16-bit WAV bytes at 24 kHz.
        :raises ValueError: If ``text`` is blank.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        speed = float(meta.get("speed") or 1.0)
        hz = _VOICE_HZ.get(str(meta.get("voice_id") or "plain"), 220.0)
        frames = int(len(text.strip()) * SECONDS_PER_CHARACTER * SAMPLE_RATE / speed)
        samples = (
            int(8000 * math.sin(2 * math.pi * hz * i / SAMPLE_RATE))
            for i in range(frames)
        )
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(b"".join(struct.pack("<h", s) for s in samples))
        return buf.getvalue()
