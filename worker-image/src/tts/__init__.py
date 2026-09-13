"""Pluggable TTS backends for Auritus workers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tts.base import TTSBackend


def get_backend(name: str) -> TTSBackend:
    """Instantiate a TTS backend by name."""
    from tts.registry import get_backend as _registry_get

    return _registry_get(name)


__all__ = ["get_backend"]
