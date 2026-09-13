"""Behave steps for Kokoro default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("a Kokoro job without an explicit voice_id")
def step_kokoro_job_no_voice(context) -> None:
    context.kokoro_meta = {}


@given('a Kokoro job with voice_id "{voice_id}"')
def step_kokoro_job_with_voice(context, voice_id: str) -> None:
    context.kokoro_meta = {"voice_id": voice_id}


@when("the Kokoro voice is resolved for synthesis")
def step_resolve_kokoro_voice(context) -> None:
    from tts.kokoro import resolve_kokoro_voice

    context.resolved_voice_id = resolve_kokoro_voice(context.kokoro_meta)


@then('the Kokoro voice_id is "{expected}"')
def step_kokoro_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
