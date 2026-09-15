"""Behave steps for Chatterbox default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("a Chatterbox job without an explicit voice_id")
def step_chatterbox_job_no_voice(context) -> None:
    context.chatterbox_meta = {}


@given('a Chatterbox job with voice_id "{voice_id}"')
def step_chatterbox_job_with_voice(context, voice_id: str) -> None:
    context.chatterbox_meta = {"voice_id": voice_id}


@given('a Chatterbox job with voice_id ""')
def step_chatterbox_job_with_empty_voice(context) -> None:
    context.chatterbox_meta = {"voice_id": ""}


@when("the Chatterbox voice is resolved for synthesis")
def step_resolve_chatterbox_voice(context) -> None:
    from tts.chatterbox import resolve_chatterbox_voice

    context.resolved_voice_id = resolve_chatterbox_voice(context.chatterbox_meta)


@then('the Chatterbox voice_id is "{expected}"')
def step_chatterbox_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
