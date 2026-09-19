"""Behave steps for TTS speech pause segmentation."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@given('a speech text "{text}"')
def step_given_speech_text(context, text: str) -> None:
    """Store input speech text in the test context.

    :param context: Behave test execution context.
    :param text: Input speech string to test.
    """
    context.speech_text = text


@when("the speech text is segmented on pauses")
def step_when_segmented_on_pauses(context) -> None:
    """Execute pause segmentation on the stored speech text.

    :param context: Behave test execution context.
    """
    from tts.breaks import split_on_pauses

    context.pause_segments = split_on_pauses(context.speech_text)


@then("the resulting pause segments are:")
def step_then_pause_segments_are(context) -> None:
    """Verify the resulting pause segments match expected table rows.

    :param context: Behave test execution context containing context.table.
    """
    expected = [row["segment"] for row in context.table]
    assert (
        context.pause_segments == expected
    ), f"Expected {expected}, got {context.pause_segments}"
