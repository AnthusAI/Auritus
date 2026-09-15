"""Behave steps for Higgs Audio v3 default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("a Higgs job without an explicit voice_id")
def step_higgs_job_no_voice(context) -> None:
    context.higgs_meta = {}


@given('a Higgs job with voice_id "{voice_id}"')
def step_higgs_job_with_voice(context, voice_id: str) -> None:
    context.higgs_meta = {"voice_id": voice_id}


@given('a Higgs job with voice_id ""')
def step_higgs_job_with_empty_voice(context) -> None:
    context.higgs_meta = {"voice_id": ""}


@when("the Higgs voice is resolved for synthesis")
def step_resolve_higgs_voice(context) -> None:
    from tts.higgs import resolve_higgs_voice

    context.resolved_voice_id = resolve_higgs_voice(context.higgs_meta)


@then('the Higgs voice_id is "{expected}"')
def step_higgs_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
