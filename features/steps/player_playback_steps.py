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


def format_duration(seconds: float) -> str:
    """Format seconds into m:ss or h:mm:ss."""
    if seconds < 0:
        return "0:00"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes}:{remaining_seconds:02d}"


@given("the player is mounted with ready audio")
def step_player_mounted_ready(context) -> None:
    context.player_ui = {
        "playing": False,
        "play_icon_visible": True,
        "pause_icon_visible": False,
        "label": "Play",
    }


@when("playback is idle")
def step_playback_idle(context) -> None:
    context.player_ui["playing"] = False
    context.player_ui["play_icon_visible"] = True
    context.player_ui["pause_icon_visible"] = False
    context.player_ui["label"] = "Play"


@then("the play button shows a play icon")
def step_button_play_icon(context) -> None:
    assert context.player_ui["play_icon_visible"] is True
    assert context.player_ui["pause_icon_visible"] is False


@then('the play button has label "{label}"')
def step_button_label(context, label: str) -> None:
    assert context.player_ui["label"] == label


@when("playback is active")
def step_playback_active(context) -> None:
    context.player_ui["playing"] = True
    context.player_ui["play_icon_visible"] = False
    context.player_ui["pause_icon_visible"] = True
    context.player_ui["label"] = "Pause"


@then("the play button shows a pause icon")
def step_button_pause_icon(context) -> None:
    assert context.player_ui["pause_icon_visible"] is True
    assert context.player_ui["play_icon_visible"] is False


@given("an audio clip with duration {seconds:d} seconds")
def step_clip_duration(context, seconds: int) -> None:
    context.clip_duration = float(seconds)
    context.clip_elapsed = 0.0


@when("{seconds:d} seconds of the clip have played")
def step_clip_elapsed(context, seconds: int) -> None:
    context.clip_elapsed = float(seconds)


@then('the elapsed time displays "{display}"')
def step_elapsed_display(context, display: str) -> None:
    formatted = format_duration(context.clip_elapsed)
    assert formatted == display, f"Expected elapsed {display}, got {formatted}"


@then('the total duration displays "{display}"')
def step_total_duration_display(context, display: str) -> None:
    formatted = format_duration(context.clip_duration)
    assert formatted == display, f"Expected duration {display}, got {formatted}"
