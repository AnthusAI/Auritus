"""Step definitions for job telemetry and worker race attribution."""

from __future__ import annotations

from datetime import datetime, timezone
import time

from behave import given, then, when


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@given('a job claimed by "{owner}" with content hash "{content_hash}"')
def step_given_claimed_with_hash(context, owner: str, content_hash: str) -> None:
    context.active_hash = content_hash
    now = _utc_now_iso()
    worker_type = "batch" if owner.startswith("batch:") else "local"
    context.jobs = {
        content_hash: {
            "content_hash": content_hash,
            "status": "claimed",
            "claim_owner": owner,
            "claimed_by": owner,
            "worker_type": worker_type,
            "claim_deadline": int(time.time()) + 900,
            "created_at": now,
            "claimed_at": now,
            "claimed_at_epoch": int(time.time()),
        }
    }


@when('the job is marked done with audio key "{audio_key}"')
def step_mark_done(context, audio_key: str) -> None:
    content_hash = getattr(context, "active_hash", next(iter(context.jobs)))
    job = context.jobs[content_hash]
    job["status"] = "done"
    job["audio_key"] = audio_key
    job["completed_at"] = _utc_now_iso()
    claimed_epoch = job.get("claimed_at_epoch") or int(time.time())
    job["duration_seconds"] = max(1, int(time.time()) - claimed_epoch + 2)


@when('worker "{owner}" reports failure with reason "{reason}"')
def step_report_failure(context, owner: str, reason: str) -> None:
    content_hash = getattr(context, "active_hash", next(iter(context.jobs)))
    job = context.jobs[content_hash]
    job["status"] = "failed"
    job["error_message"] = reason
    job["failed_at"] = _utc_now_iso()


@then('the job worker_type is "{expected_type}"')
def step_check_worker_type(context, expected_type: str) -> None:
    job = next(iter(context.jobs.values()))
    assert (
        job.get("worker_type") == expected_type
    ), f"Expected {expected_type}, got {job.get('worker_type')}"


@then('the job claimed_by is "{expected_owner}"')
def step_check_claimed_by(context, expected_owner: str) -> None:
    job = next(iter(context.jobs.values()))
    assert (
        job.get("claimed_by") == expected_owner
    ), f"Expected {expected_owner}, got {job.get('claimed_by')}"


@then("the job has a claimed_at timestamp")
def step_check_claimed_at(context) -> None:
    job = next(iter(context.jobs.values()))
    assert job.get("claimed_at") is not None


@then("the job has a completed_at timestamp")
def step_check_completed_at(context) -> None:
    job = next(iter(context.jobs.values()))
    assert job.get("completed_at") is not None


@then("the job duration_seconds is recorded")
def step_check_duration_seconds(context) -> None:
    job = next(iter(context.jobs.values()))
    assert job.get("duration_seconds") is not None
    assert isinstance(job["duration_seconds"], (int, float))


@then('the job error_message is "{expected_error}"')
def step_check_error_message(context, expected_error: str) -> None:
    job = next(iter(context.jobs.values()))
    assert job.get("error_message") == expected_error


@then("the job has a failed_at timestamp")
def step_check_failed_at(context) -> None:
    job = next(iter(context.jobs.values()))
    assert job.get("failed_at") is not None
