"""Step definitions for the unfiltered admin job listing spec."""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import boto3
from behave import given, then, when


def _operator_headers() -> dict[str, str]:
    """Return valid operator auth headers."""
    return {"authorization": "Bearer test-operator-token-12345"}


def _ensure_handler_loaded(context) -> None:
    """Load the router handler module if not already loaded."""
    sys.modules.pop("handler", None)
    handler_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "router"
    )
    if handler_path not in sys.path:
        sys.path.insert(0, handler_path)
    handler = importlib.import_module("handler")
    handler._sfn = Mock()
    handler._batch = Mock()
    context.handler_module = handler


def _ensure_aws_mocks(context) -> None:
    """Initialize moto mocks and DynamoDB tables if not already done."""
    from moto import mock_aws

    if not hasattr(context, "jobs_table") or context.jobs_table is None:
        if hasattr(context, "_mock_aws"):
            try:
                context._mock_aws.__exit__(None, None, None)
            except Exception:
                pass

        context._mock_aws = mock_aws()
        context._mock_aws.__enter__()

        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "content_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "content_hash", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "status-created_at-index",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="sites",
            KeySchema=[{"AttributeName": "site_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "site_id", "AttributeType": "S"},
                {"AttributeName": "site_key", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "site_key-index",
                    "KeySchema": [{"AttributeName": "site_key", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="audio")

        os.environ.update(
            {
                "JOBS_TABLE": "jobs",
                "SITES_TABLE": "sites",
                "AUDIO_BUCKET": "audio",
                "CLOUDFRONT_DOMAIN": "audio.example.com",
                "FALLBACK_STATE_MACHINE_ARN": "",
                "FALLBACK_SECONDS": "900",
                "DAILY_SITE_QUOTA": "100",
                "BATCH_JOB_QUEUE_NAME": "test-queue",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )

        context.jobs_table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "jobs"
        )
        context.sites_table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "sites"
        )
        context.s3_client = s3
        # Deliberately not setting a permanent "_aws_mocks_initialized" flag
        # here: behave's Context stores underscore-prefixed attributes
        # directly on the context object rather than the per-scenario layer
        # stack, so such a flag survives long after this scenario's own
        # non-underscore attributes (jobs_table included) are popped and
        # gone. A later feature file gating its own setup on that same name
        # (job_backend_integrity_steps.py does) would then skip creating its
        # own jobs_table entirely. This function already gates correctly on
        # jobs_table itself, which behave does scope per scenario.


def _build_event(
    method: str, path: str, *, headers: dict[str, str], query: dict[str, str] | None
) -> dict:
    """Build an API Gateway HTTP API v2 event."""
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "headers": headers,
        "body": None,
        "pathParameters": None,
        "queryStringParameters": query,
    }


@given("eight jobs spread across every status with staggered creation times")
def step_eight_staggered_jobs(context) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    # Five older jobs, spread across pending/claimed/failed. Named "aaa-*" so
    # they sort first by content_hash -- moto's Scan (like real DynamoDB's)
    # does not honor insertion or creation order, and a naive unfiltered
    # listing built on Scan(Limit=N) returns items in whatever order the
    # table's own partitioning happens to produce. Using hash values that
    # collate before the newest jobs below reproduces that: against the
    # pre-fix Scan-based implementation, a Limit=3 scan reads exactly these
    # five's prefix first and never reaches the genuinely newest jobs at all.
    older = [
        ("aaa-older-pending-1", "pending", 0),
        ("aaa-older-claimed-1", "claimed", 1),
        ("aaa-older-failed-1", "failed", 2),
        ("aaa-older-pending-2", "pending", 3),
        ("aaa-older-claimed-2", "claimed", 4),
    ]
    for content_hash, status, offset_minutes in older:
        context.jobs_table.put_item(
            Item={
                "content_hash": content_hash,
                "status": status,
                "tts_backend": "kokoro",
                "voice_id": "af_heart",
                "text": "Older job",
                "name": "",
                "byline": "",
                "site_key": "test-key",
                "site_id": "site-1",
                "job_token": "token",
                "created_at": (base + timedelta(minutes=offset_minutes)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "updated_at": (base + timedelta(minutes=offset_minutes)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        )

    context.newest_hashes = [
        "zzz-newest-done-1",
        "zzz-newest-done-2",
        "zzz-newest-done-3",
    ]
    for index, content_hash in enumerate(context.newest_hashes):
        created_at = (base + timedelta(minutes=100 + index)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        context.jobs_table.put_item(
            Item={
                "content_hash": content_hash,
                "status": "done",
                "tts_backend": "kokoro",
                "voice_id": "af_heart",
                "text": "Newest job",
                "name": "",
                "byline": "",
                "site_key": "test-key",
                "site_id": "site-1",
                "job_token": "token",
                "created_at": created_at,
                "updated_at": created_at,
                "audio_key": f"audio/{content_hash}.wav",
            }
        )
        context.jobs_table_last_created_at = created_at


@given('the three most recently created jobs all have status "done"')
def step_newest_are_done(context) -> None:
    # Enforced by construction in the previous step; this step documents the
    # scenario's precondition for readability.
    assert len(context.newest_hashes) == 3


@when("the operator requests the unfiltered job list with limit {limit:d}")
def step_request_unfiltered_list(context, limit: int) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "GET",
        "/admin/jobs",
        headers=_operator_headers(),
        query={"limit": str(limit)},
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = json.loads(context.response["body"])


@then("the response contains exactly the 3 most recently created jobs")
def step_check_newest_jobs(context) -> None:
    returned_hashes = [job["content_hash"] for job in context.response_body["jobs"]]
    assert len(returned_hashes) == 3, f"Expected 3 jobs, got {len(returned_hashes)}"
    assert set(returned_hashes) == set(
        context.newest_hashes
    ), f"Expected the newest jobs {context.newest_hashes}, got {returned_hashes}"


@then("those jobs are ordered from newest to oldest")
def step_check_order(context) -> None:
    created_at_values = [job["created_at"] for job in context.response_body["jobs"]]
    assert created_at_values == sorted(created_at_values, reverse=True)


@given("twelve jobs spread across every status with staggered creation times")
def step_twelve_staggered_jobs(context) -> None:
    """Create 12 jobs cycling through every status with distinct, strictly
    increasing ``created_at`` values, so the newest-to-oldest ordering is
    unambiguous and the four-way status merge has to be exercised across
    multiple pages (12 jobs / limit 5 = 3 pages).
    """
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    base = datetime(2026, 2, 1, tzinfo=timezone.utc)
    statuses = ["pending", "claimed", "done", "failed"]
    context.all_job_hashes = []
    context.all_job_texts = {}
    for index in range(12):
        content_hash = f"page-job-{index:03d}"
        status = statuses[index % len(statuses)]
        created_at = (base + timedelta(minutes=index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        text = f"Job number {index}"
        context.jobs_table.put_item(
            Item={
                "content_hash": content_hash,
                "status": status,
                "tts_backend": "kokoro",
                "voice_id": "af_heart",
                "text": text,
                "name": "",
                "byline": "",
                "site_key": "test-key",
                "site_id": "site-1",
                "job_token": "token",
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        context.all_job_hashes.append(content_hash)
        context.all_job_texts[content_hash] = text

    # Jobs were created oldest-first above, so the newest-to-oldest order
    # is simply the reverse of creation order.
    context.expected_newest_to_oldest = list(reversed(context.all_job_hashes))


@when("the operator pages through the unfiltered job list with limit {limit:d}")
def step_page_through_unfiltered_list(context, limit: int) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    pages: list[list[dict]] = []
    next_token = None
    guard = 0
    while True:
        guard += 1
        assert guard < 50, "Pagination did not terminate -- possible infinite loop"
        query = {"limit": str(limit)}
        if next_token:
            query["next_token"] = next_token
        event = _build_event(
            "GET",
            "/admin/jobs",
            headers=_operator_headers(),
            query=query,
        )
        response = context.handler_module.handler(event, None)
        body = json.loads(response["body"])
        pages.append(body["jobs"])
        next_token = body.get("next_token")
        if not next_token:
            break

    context.paged_responses = pages


@then("every page but the last contains exactly {limit:d} jobs")
def step_check_page_sizes(context, limit: int) -> None:
    pages = context.paged_responses
    assert len(pages) > 1, "Expected pagination to require more than one page"
    for page in pages[:-1]:
        assert (
            len(page) == limit
        ), f"Expected {limit} jobs on a non-last page, got {len(page)}"
    assert 0 < len(pages[-1]) <= limit


@then("the jobs across all pages are exactly the twelve jobs with no duplicates")
def step_check_no_duplicates_and_completeness(context) -> None:
    all_hashes = [
        job["content_hash"] for page in context.paged_responses for job in page
    ]
    assert len(all_hashes) == len(
        set(all_hashes)
    ), f"Duplicate content_hash values found across pages: {all_hashes}"
    assert set(all_hashes) == set(context.all_job_hashes), (
        f"Expected all 12 jobs, got {sorted(all_hashes)} vs "
        f"{sorted(context.all_job_hashes)}"
    )


@then("the jobs across all pages appear in order from newest to oldest")
def step_check_global_order(context) -> None:
    all_hashes = [
        job["content_hash"] for page in context.paged_responses for job in page
    ]
    assert all_hashes == context.expected_newest_to_oldest, (
        f"Expected global newest-to-oldest order {context.expected_newest_to_oldest}, "
        f"got {all_hashes}"
    )
