"""Tests for pluggable TTS backends."""

from __future__ import annotations

from auritus.tts import get_backend
from auritus.tts.f5 import resolve_f5_voice
from auritus.tts.kokoro import resolve_kokoro_voice
from auritus.tts.qwen import resolve_qwen_voice


from auritus.tts.higgs import resolve_higgs_voice


def test_higgs_backend_name_and_generate() -> None:
    higgs = get_backend("higgs")
    assert higgs.name == "higgs"
    assert get_backend("higgs-v3").name == "higgs"
    assert get_backend("higgs3").name == "higgs"


def test_higgs_resolve_voice_defaults_to_default() -> None:
    assert resolve_higgs_voice({}) == "default"
    assert resolve_higgs_voice({"voice_id": ""}) == "default"
    assert resolve_higgs_voice({"voice_id": "default"}) == "default"
    assert resolve_higgs_voice({"voice_id": "voice_a"}) == "voice_a"


def test_higgs_backend_empty_text_raises() -> None:
    import pytest

    higgs = get_backend("higgs")
    with pytest.raises(ValueError, match="Cannot generate audio for empty text"):
        higgs.generate("", {})


def test_qwen_backend_resolves_without_generate() -> None:
    qwen = get_backend("qwen")
    assert qwen.name == "qwen"


def test_kokoro_backend_resolves_without_generate() -> None:
    kokoro = get_backend("kokoro")
    assert kokoro.name == "kokoro"


def test_f5_backend_resolves_without_generate() -> None:
    f5 = get_backend("f5")
    assert f5.name == "f5"
    f5_alias = get_backend("f5-tts")
    assert f5_alias.name == "f5"


def test_kokoro_resolve_voice_defaults_to_af_heart() -> None:
    assert resolve_kokoro_voice({}) == "af_heart"
    assert resolve_kokoro_voice({"voice_id": "default"}) == "af_heart"
    assert resolve_kokoro_voice({"voice_id": "am_adam"}) == "am_adam"


def test_qwen_resolve_voice_defaults_to_ryan() -> None:
    assert resolve_qwen_voice({}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "default"}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "Chelsie"}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "Aiden"}) == "Aiden"


def test_f5_resolve_voice_defaults_to_default() -> None:
    assert resolve_f5_voice({}) == "default"
    assert resolve_f5_voice({"voice_id": ""}) == "default"
    assert resolve_f5_voice({"voice_id": "default"}) == "default"
    assert resolve_f5_voice({"voice_id": "custom_voice"}) == "custom_voice"


def test_unknown_backend_raises() -> None:
    try:
        get_backend("nope")
        assert False, "expected ValueError"
    except ValueError:
        pass
