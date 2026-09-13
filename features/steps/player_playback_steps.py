"""Behave steps for Play restarting finished audio."""

from __future__ import annotations

from behave import given, then, when


class PlaybackPosition:
    """Duck type matching embed rewindIfEnded."""

    def __init__(self, current_time: float, duration: float, ended: bool) -> None:
        self.currentTime = current_time
        self.duration = duration
        self.ended = ended


def rewind_if_ended(media: PlaybackPosition) -> None:
    """Move playback to the start when the clip has already finished."""
    duration_known = media.duration > 0
    at_end = media.ended or (duration_known and media.currentTime >= media.duration)
    if at_end:
        media.currentTime = 0


@given("generated audio duration is {seconds:d} seconds")
def step_duration(context, seconds: int) -> None:
    context.playback_duration = float(seconds)


@given("playback is at {seconds:d} seconds")
def step_at_position(context, seconds: int) -> None:
    duration = context.playback_duration
    context.playback = PlaybackPosition(
        current_time=float(seconds),
        duration=duration,
        ended=float(seconds) >= duration,
    )


@when("the listener activates Play")
def step_play(context) -> None:
    if getattr(context, "waiting_player", None) is not None:
        context.waiting_player["pending_play"] = True
        return
    rewind_if_ended(context.playback)


@given("the player is waiting for audio")
def step_waiting(context) -> None:
    context.waiting_player = {"pending_play": False, "playing": False, "ready": False}


@when("the clip becomes ready")
def step_clip_ready(context) -> None:
    context.waiting_player["ready"] = True
    if context.waiting_player["pending_play"]:
        context.waiting_player["playing"] = True


@then("playback starts")
def step_playback_starts(context) -> None:
    assert context.waiting_player["playing"] is True


@then("playback position is {seconds:d} seconds")
def step_position(context, seconds: int) -> None:
    assert context.playback.currentTime == float(seconds)
