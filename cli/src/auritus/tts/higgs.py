"""Higgs (Boson) TTS backend stub for the local worker.

The production Higgs integration loads model weights at runtime (not baked
into the CLI wheel). See ``docs/TTS_LICENSES.md`` for license and fetch policy.
"""

from __future__ import annotations

import io
import wave
from typing import Any

from auritus.tts.base import TTSBackend


class HiggsBackend(TTSBackend):
    """Higgs TTS backend. Returns a silent WAV until weights are configured."""

    name = "higgs"

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text`` using Higgs when weights are available.

        Until runtime weights are wired, returns a short silent WAV so the
        claim-generate-upload-done pipeline can be exercised end to end.

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes.
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
