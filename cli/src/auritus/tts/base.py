"""TTSBackend protocol for local worker generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TTSBackend(ABC):
    """Generate speech audio bytes from normalized page text."""

    name: str = "base"

    @abstractmethod
    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text``.

        :param text: Final TTS input string from the embed generator.
        :param meta: Job metadata (voice_id, name, byline, ...).
        :returns: Encoded audio bytes (WAV or MP3 per backend).
        """
