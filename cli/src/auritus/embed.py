"""Embed snippet helpers for site and player commands."""

from __future__ import annotations

import re

_SITE_KEY_RE = re.compile(r'data-auritus-site-key=["\']([^"\']+)["\']', re.IGNORECASE)


def format_embed_snippet(
    *,
    site_key: str,
    name: str = "",
    byline: str = "",
    script_src: str = "https://aurit.us/embed.js",
) -> str:
    """Return a ready-to-paste Auritus embed ``script`` tag.

    :param site_key: Deployer-issued site key.
    :param name: Optional clip title (cosmetic; does not affect content hash).
    :param byline: Optional byline (cosmetic).
    :param script_src: URL of the embed bundle.
    :returns: HTML snippet string.
    """
    return (
        f"<script\n"
        f'  src="{script_src}"\n'
        f'  data-auritus-site-key="{site_key}"\n'
        f'  data-auritus-name="{name}"\n'
        f'  data-auritus-byline="{byline}"\n'
        f"></script>"
    )


def verify_embed_snippet(snippet: str) -> tuple[bool, str]:
    """Validate that a snippet includes a site key and script tag.

    :param snippet: Raw HTML snippet text.
    :returns: Tuple of success flag and message.
    """
    if "data-auritus-site-key" not in snippet:
        return False, "missing data-auritus-site-key attribute"
    match = _SITE_KEY_RE.search(snippet)
    if not match or not match.group(1).strip():
        return False, "site key attribute is empty"
    if "<script" not in snippet.lower():
        return False, "missing script element"
    return True, "ok"
