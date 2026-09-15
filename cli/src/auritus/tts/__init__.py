"""Pluggable TTS backends for the local worker daemon."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auritus.tts.base import TTSBackend


def get_backend(name: str) -> TTSBackend:
    """Instantiate a TTS backend by name.

    :param name: Backend key (``higgs``, ``qwen``, ``kokoro``, …).
    :returns: Backend instance.
    :raises ValueError: If the name is unknown.
    """
    key = (name or "").strip().lower()
    if key in ("higgs", "higgs-v3", "higgs3"):
        from auritus.tts.higgs import HiggsBackend

        return HiggsBackend()
    if key == "qwen":
        from auritus.tts.qwen import QwenBackend

        return QwenBackend()
    if key == "kokoro":
        from auritus.tts.kokoro import KokoroBackend

        return KokoroBackend()
    if key == "fish":
        from auritus.tts.fish import FishBackend

        return FishBackend()
    if key == "coqui":
        from auritus.tts.coqui import CoquiBackend

        return CoquiBackend()
    if key == "bark":
        from auritus.tts.bark import BarkBackend

        return BarkBackend()
    if key in ("f5", "f5-tts"):
        from auritus.tts.f5 import F5Backend

        return F5Backend()
    if key in ("chatterbox", "chatterbox-tts"):
        from auritus.tts.chatterbox import ChatterboxBackend

        return ChatterboxBackend()
    raise ValueError(
        f"Unknown TTS backend: {name!r}. "
        "Known: ['bark', 'chatterbox', 'coqui', 'f5', 'fish', 'higgs', 'kokoro', 'qwen']"
    )


__all__ = [
    "get_backend",
]
