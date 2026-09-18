"""Step definitions for voice selection and fine-grained voice markup."""

from __future__ import annotations

import importlib
import os
import sys
from html.parser import HTMLParser

from behave import given, then, when

from auritus.tts.breaks import (
    AURITUS_BREAK_MARKER,
    AURITUS_VOICE_RESET_MARKER,
    parse_voiced_segments,
)
from common_steps import _hash


def _resolve_voice_id(voice_id: str | None, backend: str) -> str:
    os.environ.setdefault("JOBS_TABLE", "test-jobs")
    os.environ.setdefault("SITES_TABLE", "test-sites")
    os.environ.setdefault("AUDIO_BUCKET", "test-bucket")
    handler_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "router"
    )
    if handler_path not in sys.path:
        sys.path.insert(0, handler_path)
    handler = importlib.import_module("handler")
    return handler._resolve_voice_id(voice_id, backend)


class _VoicedDOMExtractor(HTMLParser):
    """Simulate client-side generator extraction with voice markers."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._voice_stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        voice = None
        for key, value in attrs:
            if key == "data-auritus-voice" and value:
                voice = value.strip()
                break
        self._voice_stack.append(voice)
        if voice:
            self.parts.append(f"[[auritus:voice:{voice}]]")

    def handle_endtag(self, tag: str) -> None:
        if self._voice_stack:
            voice = self._voice_stack.pop()
            if voice:
                self.parts.append(AURITUS_VOICE_RESET_MARKER)

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


def _extract_voiced_dom(html: str) -> str:
    extractor = _VoicedDOMExtractor()
    extractor.feed(html)
    return " ".join(extractor.parts)


@given('an embed tag with tts_backend "{backend}" and data-auritus-voice "{voice}"')
def step_embed_with_voice(context, backend: str, voice: str) -> None:
    context.embed_backend = backend
    context.embed_voice = voice


@given('an embed tag with tts_backend "{backend}" and no data-auritus-voice attribute')
def step_embed_without_voice(context, backend: str) -> None:
    context.embed_backend = backend
    context.embed_voice = None


@when("the embed configuration is parsed")
def step_parse_embed_config(context) -> None:
    context.resolved_voice = _resolve_voice_id(
        context.embed_voice, context.embed_backend
    )


@then('the resolved voice_id is "{expected_voice}"')
def step_assert_resolved_voice(context, expected_voice: str) -> None:
    assert (
        context.resolved_voice == expected_voice
    ), f"Expected {expected_voice!r}, got {context.resolved_voice!r}"


@given(
    'an article containing standard text and an element with data-auritus-voice "{voice}"'
)
def step_article_with_voice_markup(context, voice: str) -> None:
    context.root_html = (
        f"<article><p>Standard narrative.</p>"
        f'<blockquote data-auritus-voice="{voice}">Quoted speech.</blockquote>'
        f"</article>"
    )


@then('the TTS text contains voice marker "{marker}"')
def step_tts_contains_voice_marker(context, marker: str) -> None:
    assert marker in context.tts_text, f"Marker {marker!r} not in {context.tts_text!r}"


@then('the TTS text contains voice reset marker "{marker}"')
def step_tts_contains_voice_reset(context, marker: str) -> None:
    assert marker in context.tts_text, f"Reset {marker!r} not in {context.tts_text!r}"


@given(
    'TTS text containing standard speech and a marked voice segment "{marked_segment}"'
)
def step_given_voiced_tts_text(context, marked_segment: str) -> None:
    context.tts_text = f"Standard speech {AURITUS_BREAK_MARKER} {marked_segment}"


@when('the backend parses voiced segments with default voice "{default_voice}"')
def step_backend_parses_voiced_segments(context, default_voice: str) -> None:
    context.parsed_segments = parse_voiced_segments(context.tts_text, default_voice)


@then('the parsed segments contain text "{snippet}" with voice "{voice}"')
def step_assert_voiced_segment(context, snippet: str, voice: str) -> None:
    found = any(
        snippet in text and seg_voice == voice
        for text, seg_voice in context.parsed_segments
    )
    assert (
        found
    ), f"Segment ({snippet!r}, {voice!r}) not found in {context.parsed_segments}"


@given('article text "{text}"')
def step_given_article_text(context, text: str) -> None:
    context.article_text = text


@when(
    'content hashes are computed for backend "{backend}" with voice "{voice1}" and voice "{voice2}"'
)
def step_compute_hashes_two_voices(
    context, backend: str, voice1: str, voice2: str
) -> None:
    context.hash1 = _hash(context.article_text, voice1, backend)
    context.hash2 = _hash(context.article_text, voice2, backend)


@then("the content hashes are distinct")
def step_hashes_distinct(context) -> None:
    assert (
        context.hash1 != context.hash2
    ), f"Hashes should be distinct but both are {context.hash1}"


@given('plain article text "{text}"')
def step_plain_text(context, text: str) -> None:
    context.plain_text = text


@given('voiced article text "{text}"')
def step_voiced_text(context, text: str) -> None:
    context.voiced_text = text


@when(
    'content hashes are computed for both texts with backend "{backend}" and default voice "{voice}"'
)
def step_compute_hashes_voiced_vs_plain(context, backend: str, voice: str) -> None:
    context.hash1 = _hash(context.plain_text, voice, backend)
    context.hash2 = _hash(context.voiced_text, voice, backend)
