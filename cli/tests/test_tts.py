"""Tests for pluggable TTS backends."""

from __future__ import annotations

from auritus.tts import get_backend


def test_higgs_backend_name_and_stub_generate() -> None:
    higgs = get_backend("higgs")
    assert higgs.name == "higgs"
    assert higgs.generate("hello", {}) != b""


def test_qwen_backend_resolves_without_generate() -> None:
    qwen = get_backend("qwen")
    assert qwen.name == "qwen"


def test_kokoro_backend_resolves_without_generate() -> None:
    kokoro = get_backend("kokoro")
    assert kokoro.name == "kokoro"


def test_unknown_backend_raises() -> None:
    try:
        get_backend("nope")
        assert False, "expected ValueError"
    except ValueError:
        pass
