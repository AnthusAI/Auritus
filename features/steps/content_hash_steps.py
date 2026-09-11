"""Behave steps for content hash scope scenarios."""

from __future__ import annotations

from behave import then, when

from common_steps import _hash  # noqa: F401  # used below via context helpers


@when('the TTS text becomes "{text}"')
def step_text_becomes(context, text: str) -> None:
    context.tts_text = text


@when("the content hash is computed again")
def step_compute_again(context) -> None:
    from common_steps import _hash as hash_fn

    context.hash_other = hash_fn(
        context.tts_text, context.voice_id, context.tts_backend
    )


@then("the two content hashes match")
def step_hashes_match(context) -> None:
    assert context.hash == context.hash_other
