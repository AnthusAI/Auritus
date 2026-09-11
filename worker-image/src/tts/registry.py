"""Select a TTS backend implementation by name."""

from __future__ import annotations

from tts.base import TTSBackend
from tts.higgs import HiggsBackend
from tts.qwen import QwenBackend

_BACKENDS: dict[str, type[TTSBackend]] = {
    "higgs": HiggsBackend,
    "qwen": QwenBackend,
}


def get_backend(name: str) -> TTSBackend:
    """Instantiate a backend by name.

    :param name: Backend key (``higgs`` or ``qwen``).
    :raises ValueError: If the name is unknown.
    """
    key = (name or "").strip().lower()
    if key not in _BACKENDS:
        known = ", ".join(sorted(_BACKENDS))
        raise ValueError(f"Unknown TTS backend: {name!r}. Known: {known}")
    return _BACKENDS[key]()
