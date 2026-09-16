"""Behave steps for Fish Speech default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("a Fish job without an explicit voice_id")
def step_fish_job_no_voice(context) -> None:
    context.fish_meta = {}


@given('a Fish job with voice_id "{voice_id}"')
def step_fish_job_with_voice(context, voice_id: str) -> None:
    context.fish_meta = {"voice_id": voice_id}


@given('a Fish job with voice_id ""')
def step_fish_job_with_empty_voice(context) -> None:
    context.fish_meta = {"voice_id": ""}


@when("the Fish voice is resolved for synthesis")
def step_resolve_fish_voice(context) -> None:
    from tts.fish import resolve_fish_voice

    context.resolved_voice_id = resolve_fish_voice(context.fish_meta)


@then('the Fish voice_id is "{expected}"')
def step_fish_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
