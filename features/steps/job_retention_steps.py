"""Step definitions for job/audio retention (RETENTION_DAYS / ttl)."""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from unittest.mock import Mock

import boto3
from behave import given, then, when
from moto import mock_aws

RETENTION_TOLERANCE_SECONDS = 60


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _operator_headers() -> dict[str, str]:
    """Return valid operator auth headers.

    Also satisfies ``_check_job_token``'s "Authorization: Bearer <token>"
    fallback path for the non-admin ``/done`` route -- it just won't match
    any real job token, so ``_mark_done``/``_mark_failed`` fall through to
    ``_require_operator``, which only checks that a bearer token is present.
    """
    return {"authorization": "Bearer test-operator-token-12345"}


def _ensure_handler_loaded(context) -> None:
    """(Re)load the router handler module against the current env vars.

    Unlike ``_ensure_aws_mocks`` below, this is called before every request
    so a ``RETENTION_DAYS`` change from one scenario's Given step is always
    picked up fresh -- the handler module reads ``os.environ`` once at
    import time, so a stale cached import would silently keep using the
    previous scenario's retention setting.
    """
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
                "FALLBACK_STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:fallback",
                "FALLBACK_SECONDS": "900",
                "DAILY_SITE_QUOTA": "100",
                "BATCH_JOB_QUEUE_NAME": "test-queue",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )

        sites = boto3.resource("dynamodb", region_name="us-east-1").Table("sites")
        sites.put_item(
            Item={
                "site_id": "site-retention",
                "site_key": "test-key-retention",
                "origin": "https://example.com",
                "allowed_origins": ["https://example.com"],
                "daily_quota": 100,
                "disabled": False,
            }
        )

        context.jobs_table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "jobs"
        )
        context.sites_table = sites
        context.s3_client = boto3.client("s3", region_name="us-east-1")


def _build_event(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    path_parameters: dict[str, str] | None = None,
) -> dict:
    """Build an API Gateway HTTP API v2 event."""
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "headers": headers or {},
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": path_parameters,
        "queryStringParameters": None,
    }


def _decode_response_body(response: dict) -> dict:
    return json.loads(response["body"])


@given("the retention period is ninety days")
def step_retention_ninety_days(context) -> None:
    """Set RETENTION_DAYS=90 before the handler is (re)loaded.

    Stashed on ``context`` too, so later Then steps can compute the
    expected expiry window without hardcoding "90" twice.
    """
    os.environ["RETENTION_DAYS"] = "90"
    context.retention_days = 90


@given("the retention period is disabled")
def step_retention_disabled(context) -> None:
    """Set RETENTION_DAYS=0 (retention disabled) before the handler loads."""
    os.environ["RETENTION_DAYS"] = "0"
    context.retention_days = 0


@when("a job is marked done")
def step_mark_job_done(context) -> None:
    """Create a claimed job and mark it done via PUT /jobs/{hash}/done."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    content_hash = "test-job-hash-retention-001"
    context.job_content_hash = content_hash
    now_epoch = int(time.time())
    context.jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Test text for retention",
            "name": "Test Job",
            "byline": "Test Author",
            "site_key": "test-key-retention",
            "site_id": "site-retention",
            "job_token": "test-token-retention-001",
            "claimed_by": "local:worker-1",
            "claimed_at": _utc_now_iso(),
            "claimed_at_epoch": now_epoch,
            "worker_type": "local",
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
        }
    )

    context.mark_done_at_epoch = int(time.time())
    event = _build_event(
        "PUT",
        f"/jobs/{content_hash}/done",
        headers=_operator_headers(),
        body={"audio_key": f"audio/{content_hash}.wav"},
        path_parameters={"hash": content_hash},
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)
    assert context.response["statusCode"] == 200, (
        f"Expected 200 marking job done, got {context.response['statusCode']}: "
        f"{context.response_body}"
    )


@then("the job record carries an expiry ninety days in the future")
def step_verify_expiry_ninety_days(context) -> None:
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    assert "ttl" in item, "Expected a ttl attribute, but none was set"

    expected = context.mark_done_at_epoch + 90 * 86400
    actual = int(item["ttl"])
    assert (
        abs(actual - expected) <= RETENTION_TOLERANCE_SECONDS
    ), f"Expected ttl near {expected} (90 days from completion), got {actual}"


@then("the job record carries no expiry")
def step_verify_no_expiry(context) -> None:
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    assert "ttl" not in item, f"Expected no ttl attribute, but found {item.get('ttl')}"


@given("a job was marked done sixty days ago with an expiry from that completion")
def step_job_done_sixty_days_ago_with_expiry(context) -> None:
    """Seed a job record as if _mark_done had run 60 days ago under a
    90-day retention policy: status "done" and a ttl computed from that
    (past) completion time, i.e. 30 days from now -- still live, but
    stale (based on the wrong completion event) once regeneration starts
    a new lifecycle for this content hash.
    """
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    content_hash = "test-job-hash-retention-002"
    context.job_content_hash = content_hash
    completed_at_epoch = int(time.time()) - 60 * 86400
    stale_ttl = completed_at_epoch + 90 * 86400

    context.jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "done",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Test text for retention regeneration",
            "name": "Test Job",
            "byline": "Test Author",
            "site_key": "test-key-retention",
            "site_id": "site-retention",
            "job_token": "test-token-retention-002",
            "audio_key": f"audio/{content_hash}.wav",
            "completed_at": _utc_now_iso(),
            "duration_seconds": 10,
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "ttl": stale_ttl,
        }
    )
    context.s3_client.put_object(
        Bucket="audio",
        Key=f"audio/{content_hash}.wav",
        Body=b"test audio data",
    )


# Note: "the operator forces regeneration of that content hash" is already
# defined in job_regeneration_steps.py and reused as-is here -- behave
# shares one step registry across all step modules in a run, and defining
# it again (even identically) raises AmbiguousStep.


@then("the regenerated job carries no expiry")
def step_verify_regenerated_no_expiry(context) -> None:
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    assert "ttl" not in item, f"Expected no ttl attribute, but found {item.get('ttl')}"
