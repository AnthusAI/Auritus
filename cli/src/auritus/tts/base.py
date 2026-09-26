"""TTSBackend protocol for local worker generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BackendUnavailable(RuntimeError):
    """A speech backend cannot run here, so no audio was produced.

    Raised instead of returning stand-in audio, so a missing model library or
    an unsupported machine can never pass for a successful result.

    :param backend: Backend name.
    :param reason: What is missing, in words.
    :param missing_module: The module that failed to import, if that is why.
    """

    def __init__(
        self, backend: str, reason: str, missing_module: str | None = None
    ) -> None:
        super().__init__(f"The {backend!r} speech backend is unavailable: {reason}")
        self.backend = backend
        self.reason = reason
        self.missing_module = missing_module

    @classmethod
    def from_import_error(cls, backend: str, exc: ImportError) -> BackendUnavailable:
        """Describe a failed import of one of the backend's libraries.

        :param backend: Backend name.
        :param exc: The import failure.
        :returns: The error to raise (``from exc``).
        """
        module = exc.name or str(exc)
        return cls(backend, f"missing Python module {module!r}", missing_module=module)


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
