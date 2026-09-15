"""Select a TTS backend implementation by name."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tts.base import TTSBackend


def get_backend(name: str) -> TTSBackend:
    """Instantiate a backend by name.

    :param name: Backend key (``higgs``, ``qwen``, ``kokoro``, …).
    :raises ValueError: If the name is unknown.
    """
    key = (name or "").strip().lower()
    if key in ("higgs", "higgs-v3", "higgs3"):
        from tts.higgs import HiggsBackend

        return HiggsBackend()
    if key == "qwen":
        from tts.qwen import QwenBackend

        return QwenBackend()
    if key == "kokoro":
        from tts.kokoro import KokoroBackend

        return KokoroBackend()
    if key == "fish":
        from tts.fish import FishBackend

        return FishBackend()
    if key == "coqui":
        from tts.coqui import CoquiBackend

        return CoquiBackend()
    if key == "bark":
        from tts.bark import BarkBackend

        return BarkBackend()
    if key in ("f5", "f5-tts"):
        from tts.f5 import F5Backend

        return F5Backend()
    if key in ("chatterbox", "chatterbox-tts"):
        from tts.chatterbox import ChatterboxBackend

        return ChatterboxBackend()
    raise ValueError(
        f"Unknown TTS backend: {name!r}. "
        "Known: bark, chatterbox, coqui, f5, fish, higgs, kokoro, qwen"
    )
