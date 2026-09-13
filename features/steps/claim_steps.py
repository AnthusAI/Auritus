"""In-memory mutex model steps for claim behavior specs."""

from __future__ import annotations

import time

from behave import given, then, when


@given('a pending job with content hash "{content_hash}"')
def step_pending(context, content_hash: str) -> None:
    context.active_hash = content_hash
    context.jobs = {
        content_hash: {
            "content_hash": content_hash,
            "status": "pending",
            "claim_owner": None,
            "claim_deadline": None,
        }
    }
    context.last_claim = None


@given('a job claimed by "{owner}" with a fresh claim deadline')
def step_claimed(context, owner: str) -> None:
    content_hash = getattr(context, "active_hash", "abc123")
    context.jobs = {
        content_hash: {
            "content_hash": content_hash,
            "status": "claimed",
            "claim_owner": owner,
            "claim_deadline": int(time.time()) + 900,
        }
    }
    context.last_claim = None


@given('a job claimed by "{owner}" with an expired claim deadline')
def step_stale_claim(context, owner: str) -> None:
    content_hash = getattr(context, "active_hash", "abc123")
    context.jobs = {
        content_hash: {
            "content_hash": content_hash,
            "status": "claimed",
            "claim_owner": owner,
            "claim_deadline": int(time.time()) - 60,
        }
    }
    context.last_claim = None


def _claim(jobs: dict, content_hash: str, owner: str) -> dict:
    job = jobs[content_hash]
    now = int(time.time())
    if job["status"] == "pending" or (
        job["status"] == "claimed"
        and job["claim_deadline"] is not None
        and job["claim_deadline"] < now
    ):
        job["status"] = "claimed"
        job["claim_owner"] = owner
        job["claimed_by"] = owner
        job["worker_type"] = "batch" if owner.startswith("batch:") else "local"
        job["claimed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
        job["claim_deadline"] = now + 900
        return {"ok": True, "job": job}
    return {"ok": False, "job": job}


@when('worker "{owner}" claims the job')
def step_claim(context, owner: str) -> None:
    content_hash = next(iter(context.jobs))
    context.last_claim = _claim(context.jobs, content_hash, owner)


@then('the job status is "{status}"')
def step_status(context, status: str) -> None:
    job = next(iter(context.jobs.values()))
    assert job["status"] == status


@then('the claim owner is "{owner}"')
def step_owner(context, owner: str) -> None:
    job = next(iter(context.jobs.values()))
    assert job["claim_owner"] == owner


@then("the claim is rejected")
def step_rejected(context) -> None:
    assert context.last_claim is not None
    assert context.last_claim["ok"] is False
