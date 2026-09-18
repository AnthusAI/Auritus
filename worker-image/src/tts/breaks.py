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

import re

AURITUS_BREAK_MARKER = "[[auritus:break]]"
AURITUS_VOICE_RESET_MARKER = "[[auritus:voice:reset]]"
_VOICE_TOKEN_REGEX = re.compile(r"(\[\[auritus:voice:[^\]]+\]\]|\[\[auritus:break\]\])")
_VOICE_MARKER_STRIP_REGEX = re.compile(r"\[\[auritus:voice:[^\]]+\]\]")


def split_on_breaks(text: str) -> list[str]:
    """Split TTS input into segments on the block-boundary pause marker.

    Strips any embedded voice markers so backends that do not support
    multi-speaker synthesis do not synthesize the marker strings phonetically.

    :param text: Full TTS input, possibly containing AURITUS_BREAK_MARKER.
    :returns: Non-empty, trimmed segments in original order.
    """
    cleaned = _VOICE_MARKER_STRIP_REGEX.sub("", text)
    segments = [s.strip() for s in cleaned.split(AURITUS_BREAK_MARKER)]
    return [s for s in segments if s]


def parse_voiced_segments(text: str, default_voice: str) -> list[tuple[str, str]]:
    """Parse TTS input into (text_block, voice_id) segments.

    Handles inline voice markers ([[auritus:voice:<id>]] and [[auritus:voice:reset]])
    and block break markers ([[auritus:break]]).

    :param text: Full TTS input.
    :param default_voice: Default voice identifier to use for unannotated text.
    :returns: List of (segment_text, voice_id) tuples in original order.
    """
    tokens = _VOICE_TOKEN_REGEX.split(text)
    current_voice = default_voice
    results: list[tuple[str, str]] = []

    for token in tokens:
        token_strip = token.strip()
        if not token_strip or token_strip == AURITUS_BREAK_MARKER:
            continue
        if token_strip == AURITUS_VOICE_RESET_MARKER:
            current_voice = default_voice
            continue
        if token_strip.startswith("[[auritus:voice:") and token_strip.endswith("]]"):
            voice_id = token_strip[len("[[auritus:voice:") : -2].strip()
            if not voice_id or voice_id == "reset":
                current_voice = default_voice
            else:
                current_voice = voice_id
            continue

        results.append((token_strip, current_voice))

    return results
