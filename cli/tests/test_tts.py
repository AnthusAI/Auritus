"""Tests for pluggable TTS backends."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))

from tts import get_backend  # noqa: E402


def test_higgs_and_qwen_are_distinct_backends() -> None:
    higgs = get_backend("higgs")
    qwen = get_backend("qwen")
    assert higgs.name == "higgs"
    assert qwen.name == "qwen"
    assert higgs.generate("hello", {}) != b""
    assert qwen.generate("hello", {}) != b""


def test_unknown_backend_raises() -> None:
    try:
        get_backend("nope")
        assert False, "expected ValueError"
    except ValueError:
        pass
