"""Behave steps for Qwen default voice resolution."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given("a Qwen job without an explicit voice_id")
def step_qwen_job_no_voice(context) -> None:
    context.qwen_meta = {}


@given('a Qwen job with voice_id "{voice_id}"')
def step_qwen_job_with_voice(context, voice_id: str) -> None:
    context.qwen_meta = {"voice_id": voice_id}


@when("the Qwen voice is resolved for synthesis")
def step_resolve_qwen_voice(context) -> None:
    from tts.qwen import resolve_qwen_voice

    context.resolved_voice_id = resolve_qwen_voice(context.qwen_meta)


@then('the Qwen voice_id is "{expected}"')
def step_qwen_voice_id_is(context, expected: str) -> None:
    assert context.resolved_voice_id == expected
