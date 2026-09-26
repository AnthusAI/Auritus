"""Behave steps for Auritus content hash and TTS selection."""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))


WHITESPACE_RUN = re.compile(
    "[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+"
)


def _normalize(text: str) -> str:
    return WHITESPACE_RUN.sub(" ", unicodedata.normalize("NFC", text)).strip(" ")


def _hash(text: str, voice_id: str, tts_backend: str = "kokoro") -> str:
    payload = f"{_normalize(text)}\0{voice_id}\0{tts_backend}".encode()
    return hashlib.sha256(payload).hexdigest()


@given('the TTS text "{text}"')
def step_text(context, text: str) -> None:
    context.tts_text = text
    context.voice_id = "af_heart"
    context.tts_backend = "higgs"


@given('voice_id "{voice_id}"')
def step_voice(context, voice_id: str) -> None:
    context.voice_id = voice_id


@given('tts_backend "{backend}"')
def step_backend(context, backend: str) -> None:
    context.tts_backend = backend


@when("the content hash is computed")
def step_compute(context) -> None:
    context.hash = _hash(context.tts_text, context.voice_id, context.tts_backend)


@when("the name and byline are changed")
def step_cosmetics(context) -> None:
    context.name = "New name"
    context.byline = "New byline"


@when('tts_backend becomes "{backend}"')
def step_backend_change(context, backend: str) -> None:
    context.tts_backend = backend
    context.hash_after = _hash(context.tts_text, context.voice_id, context.tts_backend)


@then("the content hash stays the same")
def step_same(context) -> None:
    again = _hash(context.tts_text, context.voice_id, context.tts_backend)
    assert context.hash == again


@then("the content hash changes")
def step_changes(context) -> None:
    assert context.hash != context.hash_after


@given('a claimable job with tts_backend "{backend}"')
def step_job(context, backend: str) -> None:
    context.job = {
        "text": "Hello from Auritus",
        "tts_backend": backend,
        "voice_id": "af_heart",
    }


@when("the worker generates audio for the job")
def step_generate(context) -> None:
    from auritus.tts import get_backend

    backend = get_backend(context.job["tts_backend"])
    context.used_backend = backend.name
    context.audio = backend.generate(
        context.job["text"],
        {"voice_id": context.job["voice_id"]},
    )


@then("the Qwen backend is used")
def step_qwen(context) -> None:
    assert context.used_backend == "qwen"
    assert context.audio


@then("the Higgs backend is used")
def step_higgs(context) -> None:
    assert context.used_backend == "higgs"
    assert context.audio
