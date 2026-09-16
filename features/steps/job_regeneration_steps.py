"""Step definitions for job regeneration operations."""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import boto3
from behave import given, then, when
from botocore.exceptions import ClientError
from moto import mock_aws


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    # Mock external AWS service calls
    handler._sfn = Mock()
    handler._batch = Mock()
    context.handler_module = handler


def _ensure_aws_mocks(context) -> None:
    """Initialize moto mocks and DynamoDB tables if not already done."""
    if not hasattr(context, "jobs_table") or context.jobs_table is None:
        # Exit any previous mock
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

        # Create S3 bucket
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="audio")

        # Set environment variables
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

        # Create sites table and insert test site
        sites = boto3.resource("dynamodb", region_name="us-east-1").Table("sites")
        sites.put_item(
            Item={
                "site_id": "site-regeneration",
                "site_key": "test-key-regeneration",
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
        context._aws_mocks_initialized = True


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
    """Decode a router response body."""
    return json.loads(response["body"])


def _setup_job_for_regeneration(
    context,
    content_hash: str,
    status: str,
    with_audio: bool = False,
    with_token: bool = False,
) -> None:
    """Helper to create a job for regeneration tests."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.job_content_hash = content_hash
    old_token = "test-token-old-regen-" + content_hash[-4:]
    context.previous_job_token = old_token

    if with_audio:
        context.job_audio_key = f"audio/{context.job_content_hash}.wav"
        # Put an object in S3
        context.s3_client.put_object(
            Bucket="audio",
            Key=context.job_audio_key,
            Body=b"test audio data",
        )
    else:
        context.job_audio_key = None

    item = {
        "content_hash": context.job_content_hash,
        "status": status,
        "tts_backend": "kokoro",
        "voice_id": "af_heart",
        "text": "Test text for regeneration",
        "name": "Test Job",
        "byline": "Test Author",
        "site_key": "test-key-regeneration",
        "site_id": "site-regeneration",
        "job_token": old_token,
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
    }

    if with_audio:
        item["audio_key"] = context.job_audio_key
        item["completed_at"] = _utc_now_iso()
        item["duration_seconds"] = 10

    context.jobs_table.put_item(Item=item)


# Reuse the given steps from job_management_steps.py but add new ones as needed
@given("a completed job with stored audio for regeneration")
def step_create_completed_job_with_audio(context) -> None:
    """Create a completed job with audio."""
    _setup_job_for_regeneration(
        context, "test-job-hash-regen-001", "done", with_audio=True
    )


@given("a completed job for regeneration")
def step_create_completed_job(context) -> None:
    """Create a completed job without audio."""
    _setup_job_for_regeneration(
        context, "test-job-hash-regen-002", "done", with_audio=False
    )


@given("a pending job for regeneration")
def step_create_pending_job(context) -> None:
    """Create a pending job."""
    _setup_job_for_regeneration(
        context, "test-job-hash-regen-003", "pending", with_audio=False
    )


@given("a completed job with tracked token for regeneration")
def step_create_completed_job_with_token(context) -> None:
    """Create a completed job and capture its token for comparison."""
    _setup_job_for_regeneration(
        context, "test-job-hash-regen-004", "done", with_audio=False, with_token=True
    )


@when("the operator forces regeneration of that content hash")
def step_operator_regenerates_job(context) -> None:
    """Regenerate a job using operator auth."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "POST",
        f"/admin/jobs/{context.job_content_hash}/regenerate",
        headers=_operator_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@then('the regenerated job status is "{expected_status}"')
def step_verify_regenerated_job_status(context, expected_status: str) -> None:
    """Verify the regenerated job status."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    actual_status = item.get("status")
    assert (
        actual_status == expected_status
    ), f"Expected status {expected_status}, got {actual_status}"


@then("the previous audio object is removed from the audio bucket")
def step_verify_audio_deleted(context) -> None:
    """Verify the audio file no longer exists in S3."""
    try:
        context.s3_client.head_object(Bucket="audio", Key=context.job_audio_key)
        assert False, f"Audio object {context.job_audio_key} still exists in S3"
    except ClientError as exc:
        # Expected: the file should not exist
        assert exc.response["Error"]["Code"] == "404", f"Unexpected error: {exc}"


@then("the regenerated job has no audio url")
def step_verify_regenerated_no_audio_url(context) -> None:
    """Verify the regenerated job has no audio_key after regeneration."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    audio_key = item.get("audio_key")
    assert audio_key is None, f"Expected no audio_key, but found {audio_key}"


@then("the regenerated job keeps the same content hash")
def step_verify_regenerated_content_hash_unchanged(context) -> None:
    """Verify the regenerate response itself echoes the requested content hash.

    Re-reading the record under the same key it was stored at is
    vacuously true regardless of whether regeneration ran at all, so
    this asserts against the API response body instead -- proof the
    request was actually handled by the regenerate route, not merely
    that DynamoDB returns records under the key you ask for.
    """
    assert context.response["statusCode"] == 200, (
        f"Expected 200, got {context.response['statusCode']}: "
        f"{context.response_body}"
    )
    actual_hash = context.response_body.get("content_hash")
    assert (
        actual_hash == context.job_content_hash
    ), f"Expected hash {context.job_content_hash}, got {actual_hash}"


@then("the response is a conflict")
def step_verify_response_conflict(context) -> None:
    """Verify response status is 409."""
    assert (
        context.response["statusCode"] == 409
    ), f"Expected 409, got {context.response['statusCode']}"
    assert (
        context.response_body.get("error") is not None
    ), "Expected error message in response"


@then('the regenerated job status remains "{expected_status}"')
def step_verify_regenerated_job_status_unchanged(context, expected_status: str) -> None:
    """Verify the job status has not changed."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    actual_status = item.get("status")
    assert (
        actual_status == expected_status
    ), f"Expected status {expected_status}, got {actual_status}"


@then("the regenerated job token is different from the previous token")
def step_verify_regenerated_job_token_changed(context) -> None:
    """Verify the job token has been changed."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    new_token = item.get("job_token")
    assert (
        new_token != context.previous_job_token
    ), f"Expected new token different from {context.previous_job_token}, but got the same"


@given("a completed Batch job with billing data and rollup flags for regeneration")
def step_create_completed_batch_job_with_billing(context) -> None:
    """Create a completed Batch job with billing data and rollup flags."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    content_hash = "test-job-hash-regen-batch-001"
    context.job_content_hash = content_hash
    old_token = "test-token-batch-" + content_hash[-4:]
    context.previous_job_token = old_token

    item = {
        "content_hash": content_hash,
        "status": "done",
        "tts_backend": "kokoro",
        "voice_id": "af_heart",
        "text": "Test text for batch job regeneration",
        "name": "Batch Job Test",
        "byline": "Test Author",
        "site_key": "test-key-regeneration",
        "site_id": "site-regeneration",
        "job_token": old_token,
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "claimed_by": "batch:test-batch-job-id-123",
        "worker_type": "batch",
        "completed_at": _utc_now_iso(),
        "audio_key": f"audio/{content_hash}.wav",
        "duration_seconds": 10,
        # Billing attributes from _mark_done and batch_telemetry
        "gpu_cost_usd": Decimal("0.00146"),
        "platform_cost_usd": Decimal("0.0005"),
        "cost_rate_usd_per_hour": Decimal("0.526"),
        "rate_card_version": "v1",
        "avoided_cost_usd": Decimal("0"),
        "avoided_cost_basis": "batch_job",
        # Batch telemetry attributes
        "batch_created_at": _utc_now_iso(),
        "batch_started_at": _utc_now_iso(),
        "batch_stopped_at": _utc_now_iso(),
        "instance_type": "g4dn.xlarge",
        "container_seconds": Decimal("5.0"),
        "provisioning_seconds": Decimal("1.0"),
        "billed_seconds": Decimal("6.0"),
        # Idempotency flags
        "platform_cost_rolled_up": True,
        "gpu_cost_rolled_up": True,
        "backend_timing_rolled_up": True,
    }

    context.jobs_table.put_item(Item=item)


@then("the regenerated job has no billing attributes")
def step_verify_no_billing_attributes(context) -> None:
    """Verify billing attributes have been removed."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"

    billing_attrs = [
        "gpu_cost_usd",
        "platform_cost_usd",
        "cost_rate_usd_per_hour",
        "rate_card_version",
        "avoided_cost_usd",
        "avoided_cost_basis",
        "batch_created_at",
        "batch_started_at",
        "batch_stopped_at",
        "instance_type",
        "container_seconds",
        "provisioning_seconds",
        "billed_seconds",
    ]

    for attr in billing_attrs:
        assert (
            attr not in item
        ), f"Expected billing attribute '{attr}' to be removed, but it still exists"


@then("the regenerated job has no rollup idempotency flags")
def step_verify_no_rollup_flags(context) -> None:
    """Verify rollup idempotency flags have been removed."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"

    rollup_flags = [
        "platform_cost_rolled_up",
        "gpu_cost_rolled_up",
        "backend_timing_rolled_up",
    ]

    for flag in rollup_flags:
        assert (
            flag not in item
        ), f"Expected rollup flag '{flag}' to be removed, but it still exists"
