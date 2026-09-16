"""Step definitions for job retry operations."""

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
from decimal import Decimal
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
                "site_id": "site-retry",
                "site_key": "test-key-retry",
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


def _setup_job_for_retry(
    context,
    content_hash: str,
    status: str,
    with_claim_deadline: bool | None = None,
) -> None:
    """Helper to create a job for retry tests.

    :param context: Behave context.
    :param content_hash: The content hash of the job.
    :param status: The job status (pending, claimed, failed).
    :param with_claim_deadline: None = no deadline, True = expired, False = live.
    """
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.job_content_hash = content_hash
    now_epoch = int(time.time())

    item = {
        "content_hash": context.job_content_hash,
        "status": status,
        "tts_backend": "kokoro",
        "voice_id": "af_heart",
        "text": "Test text for retry",
        "name": "Test Job",
        "byline": "Test Author",
        "site_key": "test-key-retry",
        "site_id": "site-retry",
        "job_token": "test-token-retry-" + content_hash[-4:],
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
    }

    if status == "claimed":
        item["claim_owner"] = "local-worker-1"
        item["claimed_by"] = "local-worker-1"
        item["worker_type"] = "local"
        item["claimed_at"] = _utc_now_iso()
        item["claimed_at_epoch"] = Decimal(now_epoch)

        if with_claim_deadline is True:
            # Expired: deadline is in the past
            item["claim_deadline"] = Decimal(now_epoch - 60)
        elif with_claim_deadline is False:
            # Live: deadline is in the future
            item["claim_deadline"] = Decimal(now_epoch + 3600)

    if status == "failed":
        item["error_message"] = "Worker crashed"
        item["failed_at"] = _utc_now_iso()
        item["worker_type"] = "local"
        item["claimed_by"] = "local-worker-1"

    context.jobs_table.put_item(Item=item)


@given("a failed job for retry")
def step_create_failed_job(context) -> None:
    """Create a failed job."""
    _setup_job_for_retry(context, "test-job-hash-retry-001", "failed")


@given("a claimed job for retry with an expired claim deadline")
def step_create_claimed_job_expired(context) -> None:
    """Create a claimed job with an expired deadline."""
    _setup_job_for_retry(
        context, "test-job-hash-retry-002", "claimed", with_claim_deadline=True
    )


@given("a claimed job for retry with a live claim deadline")
def step_create_claimed_job_live(context) -> None:
    """Create a claimed job with a live deadline."""
    _setup_job_for_retry(
        context, "test-job-hash-retry-003", "claimed", with_claim_deadline=False
    )


@given("a pending job for retry")
def step_create_pending_job(context) -> None:
    """Create a pending job."""
    _setup_job_for_retry(context, "test-job-hash-retry-004", "pending")


@when("the operator retries that content hash")
def step_operator_retries_job(context) -> None:
    """Retry a job using operator auth without force."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "POST",
        f"/admin/jobs/{context.job_content_hash}/retry",
        body={},
        headers=_operator_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@when("the operator force-retries that content hash")
def step_operator_force_retries_job(context) -> None:
    """Retry a job using operator auth with force flag."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "POST",
        f"/admin/jobs/{context.job_content_hash}/retry",
        body={"force": True},
        headers=_operator_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@then('the retried job status is "{expected_status}"')
def step_verify_retried_job_status(context, expected_status: str) -> None:
    """Verify the retried job status."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    actual_status = item.get("status")
    assert (
        actual_status == expected_status
    ), f"Expected status {expected_status}, got {actual_status}"


@then("the retried job has no error message")
def step_verify_retried_no_error_message(context) -> None:
    """Verify the retried job has no error message."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    error_message = item.get("error_message")
    assert (
        error_message is None
    ), f"Expected no error_message, but found {error_message}"


@then("the retried job has no claim owner")
def step_verify_retried_no_claim_owner(context) -> None:
    """Verify the retried job has no claim owner."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    claim_owner = item.get("claim_owner")
    claimed_by = item.get("claimed_by")
    assert claim_owner is None, f"Expected no claim_owner, but found {claim_owner}"
    assert claimed_by is None, f"Expected no claimed_by, but found {claimed_by}"


@then("the retried job is still claimed")
def step_verify_retried_job_still_claimed(context) -> None:
    """Verify the job is still in claimed status."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is not None, f"Job {context.job_content_hash} does not exist"
    actual_status = item.get("status")
    assert actual_status == "claimed", f"Expected status 'claimed', got {actual_status}"


@given("a failed job with billing data and rollup flags for retry")
def step_create_failed_job_with_billing(context) -> None:
    """Create a failed job with billing data and rollup flags."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    content_hash = "test-job-hash-retry-batch-001"
    context.job_content_hash = content_hash
    now_epoch = int(time.time())

    item = {
        "content_hash": content_hash,
        "status": "failed",
        "tts_backend": "kokoro",
        "voice_id": "af_heart",
        "text": "Test text for failed batch job retry",
        "name": "Failed Batch Job Test",
        "byline": "Test Author",
        "site_key": "test-key-retry",
        "site_id": "site-retry",
        "job_token": "test-token-retry-batch-" + content_hash[-4:],
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "error_message": "Batch job failed",
        "failed_at": _utc_now_iso(),
        "claimed_by": "batch:test-batch-job-id-456",
        "worker_type": "batch",
        "claimed_at": _utc_now_iso(),
        "claimed_at_epoch": Decimal(now_epoch - 60),
        # Billing attributes from _mark_failed and batch_telemetry
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


@then("the retried job has no billing attributes")
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


@then("the retried job has no rollup idempotency flags")
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
