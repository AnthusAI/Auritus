"""Higgs (Boson) TTS backend.

License status: see docs/TTS_LICENSES.md. Weights are fetched at runtime
(not baked into the image) until redistribution terms are confirmed.
"""

from __future__ import annotations

import io
import wave
from typing import Any

from tts.base import TTSBackend


class HiggsBackend(TTSBackend):
    """First TTS backend. Uses a silent WAV stub until weights are wired."""

    name = "higgs"

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text`` using Higgs when available.

        Until model weights are configured, returns a short silent WAV so the
        pipeline (claim -> generate -> upload -> done) can be acceptance-tested.
        """
        _ = meta
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        return _silent_wav(duration_ms=max(250, min(len(text) * 40, 5000)))


def _silent_wav(*, duration_ms: int, sample_rate: int = 22050) -> bytes:
    frames = int(sample_rate * (duration_ms / 1000.0))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()
