"""Tests for embed snippet helpers."""

from __future__ import annotations

from auritus.embed import format_embed_snippet, verify_embed_snippet


def test_format_embed_includes_attributes() -> None:
    snippet = format_embed_snippet(site_key="sk_test", name="Title", byline="Author")
    assert 'data-auritus-site-key="sk_test"' in snippet
    assert 'data-auritus-name="Title"' in snippet
    assert 'data-auritus-byline="Author"' in snippet


def test_verify_embed_snippet_ok() -> None:
    snippet = format_embed_snippet(site_key="sk_test")
    ok, message = verify_embed_snippet(snippet)
    assert ok is True
    assert message == "ok"


def test_verify_embed_snippet_missing_key() -> None:
    ok, message = verify_embed_snippet("<script></script>")
    assert ok is False
    assert "site-key" in message
