"""Step definitions for web console dashboard and job explorer UI specs."""

from __future__ import annotations

from behave import given, then, when


@given("the operator is logged into the web console")
def step_operator_logged_in(context) -> None:
    context.authenticated_operator = "operator@example.com"
    context.dashboard_state = None


@when("the dashboard overview loads")
def step_dashboard_loads(context) -> None:
    context.dashboard_state = {
        "total_jobs": 42,
        "worker_race": {"local": 35, "batch": 7},
        "batch_queue_status": "ENABLED",
    }


@then("the total job count is displayed")
def step_check_total_jobs(context) -> None:
    assert context.dashboard_state is not None
    assert context.dashboard_state.get("total_jobs") == 42


@then("the worker race split is displayed")
def step_check_worker_race(context) -> None:
    race = context.dashboard_state.get("worker_race", {})
    assert race.get("local") == 35
    assert race.get("batch") == 7


@then("the Batch queue status is displayed")
def step_check_batch_status(context) -> None:
    assert context.dashboard_state.get("batch_queue_status") == "ENABLED"


@given("the operator is on the jobs page")
def step_on_jobs_page(context) -> None:
    context.jobs_table = [
        {"hash": "h1", "status": "done", "worker_type": "local"},
        {"hash": "h2", "status": "pending", "worker_type": None},
        {"hash": "h3", "status": "done", "worker_type": "batch"},
    ]


@when('filtering by status "{status}"')
def step_filter_status(context, status: str) -> None:
    context.visible_rows = [j for j in context.jobs_table if j.get("status") == status]


@then("the table lists only completed jobs")
def step_check_completed_jobs(context) -> None:
    assert len(context.visible_rows) == 2
    for row in context.visible_rows:
        assert row["status"] == "done"


@then("each job row displays the worker attribution")
def step_check_row_attribution(context) -> None:
    for row in context.visible_rows:
        assert row.get("worker_type") in ("local", "batch")


@given("a completed job with an audio URL")
def step_completed_job_with_audio(context) -> None:
    context.selected_job = {
        "content_hash": "abc-audio-123",
        "audio_url": "https://cdn.example.com/audio/abc.mp3",
        "duration_seconds": 3.8,
    }


@when("viewing the job detail page")
def step_view_job_detail(context) -> None:
    context.rendered_detail = {
        "has_audio_player": bool(context.selected_job.get("audio_url")),
        "duration_seconds": context.selected_job.get("duration_seconds"),
    }


@then("an audio player control is rendered")
def step_check_audio_player(context) -> None:
    assert context.rendered_detail["has_audio_player"] is True


@then("the synthesis duration is displayed")
def step_check_duration_displayed(context) -> None:
    assert context.rendered_detail["duration_seconds"] == 3.8
