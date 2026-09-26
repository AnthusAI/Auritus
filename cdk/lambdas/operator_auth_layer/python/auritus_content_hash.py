"""Canonical Auritus content hash, shared by the API and operator scripts.

The content hash identifies a narration job: the SHA-256 of the normalized
text, the resolved voice ID, and the TTS backend joined by NUL characters.
The browser embed computes the same value, so every rule here must match
``embed/src/generator/hash.ts`` and ``resolveVoiceId`` in
``embed/src/index.ts`` exactly.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

WHITESPACE_RUN = re.compile(
    "[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+"
)
LONE_SURROGATE = re.compile("[\ud800-\udfff]")
DEFAULT_TTS_BACKEND = "kokoro"


def normalize_text(text: str) -> str:
    """Normalize TTS text exactly as the embed does before hashing.

    Replaces lone surrogates with U+FFFD (as the browser's UTF-8 encoder
    does), applies Unicode NFC, collapses each run of the characters
    JavaScript's ``\\s`` matches into one space, and trims.

    :param text: Raw TTS text.
    :returns: The normalized text.
    """
    text = LONE_SURROGATE.sub("\ufffd", text)
    return WHITESPACE_RUN.sub(" ", unicodedata.normalize("NFC", text)).strip(" ")


def resolve_voice_id(raw_voice: str | None, tts_backend: str) -> str:
    """Resolve the voice ID that is hashed and rendered for a backend.

    A missing or ``"default"`` voice becomes the backend's default, and
    Qwen's legacy ``"Chelsie"`` becomes ``"Ryan"``.

    :param raw_voice: The requested voice, if any.
    :param tts_backend: The TTS backend name.
    :returns: The resolved voice ID.
    """
    backend = (tts_backend or DEFAULT_TTS_BACKEND).strip().lower()
    unset = not raw_voice or raw_voice == "default"
    if backend == "kokoro":
        return "af_heart" if unset else raw_voice
    if backend == "qwen":
        return "Ryan" if unset or raw_voice == "Chelsie" else raw_voice
    if backend in ("fish", "chatterbox"):
        return "narrator" if unset else raw_voice
    return raw_voice or "default"


def content_hash(text: str, raw_voice: str | None, tts_backend: str | None) -> str:
    """Compute the canonical content hash for a narration request.

    :param text: TTS text, normalized or not.
    :param raw_voice: The requested voice, resolved with
        :func:`resolve_voice_id`.
    :param tts_backend: The TTS backend; defaults to ``kokoro`` when empty.
    :returns: Lower-case hex SHA-256.
    """
    backend = tts_backend or DEFAULT_TTS_BACKEND
    voice_id = resolve_voice_id(raw_voice, backend)
    payload = f"{normalize_text(text)}\0{voice_id}\0{backend}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
