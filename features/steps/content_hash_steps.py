"""Behave steps for content hash scope scenarios."""

from __future__ import annotations

from behave import then, when
from common_steps import _hash


@when('the TTS text becomes "{text}"')
def step_text_becomes(context, text: str) -> None:
    context.tts_text = text


@when("the content hash is computed again")
def step_compute_again(context) -> None:
    context.hash_other = _hash(
        context.tts_text, context.voice_id
    )


@then("the two content hashes match")
def step_hashes_match(context) -> None:
    assert context.hash == context.hash_other
