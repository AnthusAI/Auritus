"""Qwen 3 TTS backend for the local worker (pluggable second backend)."""

from __future__ import annotations

import io
import wave
from typing import Any

from auritus.tts.base import TTSBackend


class QwenBackend(TTSBackend):
    """Second TTS backend. Proves the pluggable abstraction.

    License status: see docs/TTS_LICENSES.md. Weights are fetched at runtime
    until redistribution terms are confirmed.
    """

    name = "qwen"

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text`` using Qwen 3 when available.

        Until model weights are configured, returns a short silent WAV so the
        pipeline can verify per-job backend selection.
        """
        _ = meta
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        return _silent_wav(duration_ms=max(300, min(len(text) * 45, 5500)))


def _silent_wav(*, duration_ms: int, sample_rate: int = 22050) -> bytes:
    frames = int(sample_rate * (duration_ms / 1000.0))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()
