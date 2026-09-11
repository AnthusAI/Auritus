"""Pluggable TTS backends for the local worker daemon."""

from __future__ import annotations

from auritus.tts.base import TTSBackend
from auritus.tts.higgs import HiggsBackend
from auritus.tts.qwen import QwenBackend


def get_backend(name: str) -> TTSBackend:
    """Instantiate a TTS backend by name.

    :param name: Backend key (``higgs`` or ``qwen``).
    :returns: Backend instance.
    :raises ValueError: If the name is unknown.
    """
    backends: dict[str, type[TTSBackend]] = {
        "higgs": HiggsBackend,
        "qwen": QwenBackend,
    }
    key = (name or "").strip().lower()
    if key not in backends:
        raise ValueError(f"Unknown TTS backend: {name!r}. Known: {sorted(backends)}")
    return backends[key]()


__all__ = ["TTSBackend", "HiggsBackend", "QwenBackend", "get_backend"]
