"""Tests for the Kokoro backend's block-boundary pause handling.

Deliberately separate from test_tts.py (which was mid-edit by another
session when this was written) -- these only exercise the pure functions
(split_on_breaks, _join_with_silence), never .generate() itself, so no
model load is required.
"""

from __future__ import annotations

import numpy as np

from auritus.tts.kokoro import (
    AURITUS_BREAK_MARKER,
    BREAK_SILENCE_SECONDS,
    _join_with_silence,
    split_on_breaks,
)


def test_split_on_breaks_separates_blocks() -> None:
    text = f"Headline{AURITUS_BREAK_MARKER}First paragraph.{AURITUS_BREAK_MARKER}Second paragraph."
    assert split_on_breaks(text) == [
        "Headline",
        "First paragraph.",
        "Second paragraph.",
    ]


def test_split_on_breaks_trims_and_drops_empty_segments() -> None:
    # A trailing marker (last block in the article) or two adjacent markers
    # (defensive, shouldn't happen given the generator's own dedup guard,
    # but the split must not manufacture an empty block either way).
    text = f"  Only block.  {AURITUS_BREAK_MARKER}{AURITUS_BREAK_MARKER}  "
    assert split_on_breaks(text) == ["Only block."]


def test_split_on_breaks_with_no_marker_returns_single_block() -> None:
    assert split_on_breaks("Just one sentence.") == ["Just one sentence."]


def test_split_on_breaks_empty_text_returns_no_blocks() -> None:
    assert split_on_breaks("") == []
    assert split_on_breaks("   ") == []


def test_join_with_silence_single_block_returned_unchanged() -> None:
    block = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    result = _join_with_silence([block], sample_rate=24000)
    np.testing.assert_array_equal(result, block)


def test_join_with_silence_inserts_real_silence_between_blocks() -> None:
    sample_rate = 24000
    block_a = np.ones(10, dtype=np.float32)
    block_b = np.full(10, 2.0, dtype=np.float32)
    result = _join_with_silence([block_a, block_b], sample_rate=sample_rate)

    expected_silence_samples = int(sample_rate * BREAK_SILENCE_SECONDS)
    assert len(result) == len(block_a) + expected_silence_samples + len(block_b)

    silence_region = result[len(block_a) : len(block_a) + expected_silence_samples]
    assert np.all(silence_region == 0)
    np.testing.assert_array_equal(result[: len(block_a)], block_a)
    np.testing.assert_array_equal(result[-len(block_b) :], block_b)


def test_join_with_silence_gap_between_every_pair_of_blocks() -> None:
    sample_rate = 24000
    blocks = [np.full(5, float(i), dtype=np.float32) for i in range(4)]
    result = _join_with_silence(blocks, sample_rate=sample_rate)

    silence_samples = int(sample_rate * BREAK_SILENCE_SECONDS)
    expected_len = sum(len(b) for b in blocks) + silence_samples * (len(blocks) - 1)
    assert len(result) == expected_len
