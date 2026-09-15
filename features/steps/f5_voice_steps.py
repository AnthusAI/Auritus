"""Behave steps for F5-TTS default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("an F5 job without an explicit voice_id")
def step_f5_job_no_voice(context) -> None:
    context.f5_meta = {}


@given('an F5 job with voice_id "{voice_id}"')
def step_f5_job_with_voice(context, voice_id: str) -> None:
    context.f5_meta = {"voice_id": voice_id}


@given('an F5 job with voice_id ""')
def step_f5_job_with_empty_voice(context) -> None:
    context.f5_meta = {"voice_id": ""}


@when("the F5 voice is resolved for synthesis")
def step_resolve_f5_voice(context) -> None:
    from tts.f5 import resolve_f5_voice

    context.resolved_voice_id = resolve_f5_voice(context.f5_meta)


@then('the F5 voice_id is "{expected}"')
def step_f5_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
