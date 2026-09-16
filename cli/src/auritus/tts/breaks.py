"""Shared block-boundary pause marker for TTS backends.

Must match embed/src/generator/hash.ts AURITUS_BREAK_MARKER exactly. The
embed generator inserts this after headings, paragraphs, list items, and
blockquotes automatically (plus wherever a page explicitly marks
data-auritus-break). Each backend splits on it and inserts its own real
silence gap between blocks -- how long that gap is stays a per-backend
choice (BREAK_SILENCE_SECONDS in each backend module, not here), since
different models and voices may reasonably want different pacing. What
must not drift between backends is the marker string and how it's split,
so those two live in exactly one place.
"""

from __future__ import annotations

AURITUS_BREAK_MARKER = "[[auritus:break]]"


def split_on_breaks(text: str) -> list[str]:
    """Split TTS input into segments on the block-boundary pause marker.

    :param text: Full TTS input, possibly containing AURITUS_BREAK_MARKER.
    :returns: Non-empty, trimmed segments in original order.
    """
    segments = [s.strip() for s in text.split(AURITUS_BREAK_MARKER)]
    return [s for s in segments if s]
