"""Unit tests for break and pause segmentation."""

from __future__ import annotations

from auritus.tts.breaks import (
    AURITUS_BREAK_MARKER,
    AURITUS_PAUSE_MARKER,
    DEFAULT_PAUSE_SILENCE_SECONDS,
    parse_voiced_segments,
    split_on_breaks,
    split_on_pauses,
)


def test_split_on_breaks_basic() -> None:
    """Verify split_on_breaks correctly splits on break markers."""
    text = f"First paragraph.{AURITUS_BREAK_MARKER}Second paragraph."
    segments = split_on_breaks(text)
    assert segments == ["First paragraph.", "Second paragraph."]


def test_split_on_pauses_emdash() -> None:
    """Verify split_on_pauses splits on em-dashes and strips whitespace."""
    text = "I was lucky — I found what I loved to do early in life."
    segments = split_on_pauses(text)
    assert segments == [
        "I was lucky",
        "I found what I loved to do early in life.",
    ]


def test_split_on_pauses_double_hyphen() -> None:
    """Verify split_on_pauses splits on ASCII double hyphens."""
    text = "We released our finest creation -- the Macintosh -- a year earlier."
    segments = split_on_pauses(text)
    assert segments == [
        "We released our finest creation",
        "the Macintosh",
        "a year earlier.",
    ]


def test_split_on_pauses_spaced_endash() -> None:
    """Verify split_on_pauses splits on spaced en-dashes but preserves numeric ranges."""
    text = "Read pages 10–20 – they are the best chapters."
    segments = split_on_pauses(text)
    assert segments == [
        "Read pages 10–20",
        "they are the best chapters.",
    ]


def test_split_on_pauses_ellipsis() -> None:
    """Verify split_on_pauses splits on unicode ellipsis and multi-dot notation."""
    text = "Wait… what was that? Keep looking... don't settle."
    segments = split_on_pauses(text)
    assert segments == [
        "Wait",
        "what was that? Keep looking",
        "don't settle.",
    ]


def test_split_on_pauses_explicit_marker() -> None:
    """Verify split_on_pauses splits on explicit auritus pause marker."""
    text = f"Hello {AURITUS_PAUSE_MARKER} world"
    segments = split_on_pauses(text)
    assert segments == ["Hello", "world"]


def test_split_on_pauses_empty_and_plain() -> None:
    """Verify edge cases for plain text and empty input."""
    assert split_on_pauses("") == []
    assert split_on_pauses("   ") == []
    assert split_on_pauses("Plain simple sentence.") == ["Plain simple sentence."]


def test_default_pause_silence_duration() -> None:
    """Verify default pause silence duration is configured appropriately."""
    assert 0.15 <= DEFAULT_PAUSE_SILENCE_SECONDS <= 0.3
