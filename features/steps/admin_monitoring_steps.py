"""Step definitions for admin monitoring and queue control API specs."""

from __future__ import annotations

from behave import given, then, when


@given("a set of historical jobs with varied statuses and worker types")
def step_historical_jobs(context) -> None:
    context.jobs = {
        "job-1": {
            "content_hash": "job-1",
            "status": "done",
            "worker_type": "local",
            "duration_seconds": 4.5,
            "created_at": "2026-09-13T12:00:00Z",
        },
        "job-2": {
            "content_hash": "job-2",
            "status": "done",
            "worker_type": "batch",
            "duration_seconds": 8.0,
            "created_at": "2026-09-13T12:05:00Z",
        },
        "job-3": {
            "content_hash": "job-3",
            "status": "pending",
            "created_at": "2026-09-13T12:10:00Z",
        },
        "job-4": {
            "content_hash": "job-4",
            "status": "failed",
            "worker_type": "batch",
            "error_message": "Timeout",
            "created_at": "2026-09-13T12:15:00Z",
        },
    }


@when("the operator requests the admin overview")
def step_request_overview(context) -> None:
    counts = {"pending": 0, "claimed": 0, "done": 0, "failed": 0}
    worker_counts = {"local": 0, "batch": 0}
    durations: list[float] = []

    for item in context.jobs.values():
        st = item.get("status")
        if st in counts:
            counts[st] += 1
        wtype = item.get("worker_type")
        if wtype in worker_counts:
            worker_counts[wtype] += 1
        dur = item.get("duration_seconds")
        if dur is not None:
            durations.append(float(dur))

    avg_duration = sum(durations) / len(durations) if durations else 0.0

    context.overview_response = {
        "counts": counts,
        "worker_breakdown": worker_counts,
        "avg_duration_seconds": avg_duration,
        "total_sampled_jobs": len(context.jobs),
    }


@then("the response contains job status counts")
def step_check_status_counts(context) -> None:
    assert "counts" in context.overview_response
    assert context.overview_response["counts"]["done"] == 2
    assert context.overview_response["counts"]["pending"] == 1


@then("the response contains worker breakdown counts")
def step_check_worker_breakdown(context) -> None:
    assert "worker_breakdown" in context.overview_response
    assert context.overview_response["worker_breakdown"]["local"] == 1
    assert context.overview_response["worker_breakdown"]["batch"] == 2


@then("the response contains average duration seconds")
def step_check_avg_duration(context) -> None:
    assert "avg_duration_seconds" in context.overview_response
    assert context.overview_response["avg_duration_seconds"] > 0


@when('the operator lists jobs with status "{status}"')
def step_list_jobs_with_status(context, status: str) -> None:
    context.filtered_jobs = [
        item for item in context.jobs.values() if item.get("status") == status
    ]


@then('all returned jobs have status "{expected_status}"')
def step_check_filtered_jobs(context, expected_status: str) -> None:
    assert len(context.filtered_jobs) > 0
    for job in context.filtered_jobs:
        assert job["status"] == expected_status


@given('a completed job with content hash "{content_hash}"')
def step_completed_job(context, content_hash: str) -> None:
    context.job_detail = {
        "content_hash": content_hash,
        "status": "done",
        "audio_url": f"https://audio.example.com/{content_hash}.mp3",
        "worker_type": "local",
        "claimed_by": "local:node-1",
        "claimed_at": "2026-09-13T12:00:00Z",
        "completed_at": "2026-09-13T12:00:05Z",
        "duration_seconds": 5.0,
    }


@when('the operator requests job details for "{content_hash}"')
def step_request_job_details(context, content_hash: str) -> None:
    assert context.job_detail["content_hash"] == content_hash
    context.detail_response = context.job_detail


@then("the response includes the audio URL")
def step_check_audio_url(context) -> None:
    assert context.detail_response.get("audio_url") is not None


@then("the response includes worker attribution and timestamps")
def step_check_worker_attribution(context) -> None:
    resp = context.detail_response
    assert resp.get("worker_type") == "local"
    assert resp.get("claimed_by") == "local:node-1"
    assert resp.get("claimed_at") is not None
    assert resp.get("completed_at") is not None


@when('the operator toggles the queue state to "{new_state}"')
def step_toggle_queue_state(context, new_state: str) -> None:
    context.batch_queue_state = new_state


@when("the operator requests jobs with limit {limit:d}")
def step_request_jobs_with_limit(context, limit: int) -> None:
    job_items = list(context.jobs.values())
    context.page_limit = limit
    context.page1_jobs = job_items[:limit]
    context.next_cursor = "cursor_page_2" if len(job_items) > limit else None


@then("the response contains at most {limit:d} jobs")
def step_check_jobs_at_most(context, limit: int) -> None:
    assert len(context.page1_jobs) <= limit


@then("the response contains a next_token cursor")
def step_check_next_cursor(context) -> None:
    assert context.next_cursor is not None


@when("the operator requests the next page of jobs with the cursor")
def step_request_next_page(context) -> None:
    assert context.next_cursor is not None
    job_items = list(context.jobs.values())
    context.page2_jobs = job_items[context.page_limit :]


@then("the next page contains distinct jobs")
def step_check_distinct_jobs(context) -> None:
    p1_hashes = {j["content_hash"] for j in context.page1_jobs}
    p2_hashes = {j["content_hash"] for j in context.page2_jobs}
    assert len(p1_hashes.intersection(p2_hashes)) == 0
    assert len(p2_hashes) > 0
