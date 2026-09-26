"""TTSBackend protocol for local worker generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class TTSBackend(ABC):
    """Generate speech audio bytes from normalized page text."""

    name: str = "base"
    #: Whether :meth:`generate` honours ``meta["speed"]``.
    supports_speed: bool = False

    def model_id(self) -> str:
        """Identify the model this backend synthesizes with on this machine.

        Recorded in provenance and folded into request keys, so it must be
        cheap: implementations must not load the model to answer.

        :returns: Model identifier (e.g. a Hugging Face repo id).
        """
        return self.name

    @abstractmethod
    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio for ``text``.

        :param text: Final TTS input string from the embed generator.
        :param meta: Job metadata (voice_id, name, byline, and ``speed`` for
            backends that set :attr:`supports_speed`).
        :returns: Encoded audio bytes (WAV or MP3 per backend).
        """
