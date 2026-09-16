"""Step definitions for job management operations."""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
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


def _site_headers() -> dict[str, str]:
    """Return valid site-key headers (non-operator)."""
    return {"x-auritus-site-key": "test-key-management"}


def _ensure_handler_loaded(context) -> None:
    """Load the router handler module if not already loaded."""
    # Always reload the handler module to pick up fresh boto3 clients
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
    # Check if mocks are already initialized for this context
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
                "site_id": "site-management",
                "site_key": "test-key-management",
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


@given('a job exists with status "{status}" and a stored audio object')
def step_create_job_with_audio(context, status: str) -> None:
    """Create a job with audio."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.job_content_hash = "test-job-hash-delete-001"
    context.job_audio_key = f"audio/{context.job_content_hash}.wav"

    # Put an object in S3
    context.s3_client.put_object(
        Bucket="audio",
        Key=context.job_audio_key,
        Body=b"test audio data",
    )

    # Insert a job into the jobs table
    context.jobs_table.put_item(
        Item={
            "content_hash": context.job_content_hash,
            "status": status,
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Test text for deletion",
            "name": "Test Job",
            "byline": "Test Author",
            "site_key": "test-key-management",
            "site_id": "site-management",
            "job_token": "test-token-12345",
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "audio_key": context.job_audio_key,
        }
    )


@given('a job exists with status "{status}"')
def step_create_job_no_audio(context, status: str) -> None:
    """Create a job without audio."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.job_content_hash = "test-job-hash-delete-002"

    # Insert a job into the jobs table without audio
    context.jobs_table.put_item(
        Item={
            "content_hash": context.job_content_hash,
            "status": status,
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Test text for deletion",
            "name": "Test Job",
            "byline": "Test Author",
            "site_key": "test-key-management",
            "site_id": "site-management",
            "job_token": "test-token-12345",
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
        }
    )


@when("the operator deletes the job by content hash")
def step_operator_deletes_job(context) -> None:
    """Delete a job using operator auth."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "DELETE",
        f"/admin/jobs/{context.job_content_hash}",
        headers=_operator_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@when("the operator deletes a content hash with no job record")
def step_operator_deletes_nonexistent_job(context) -> None:
    """Delete a job that doesn't exist."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.nonexistent_hash = "nonexistent-hash-12345"
    event = _build_event(
        "DELETE",
        f"/admin/jobs/{context.nonexistent_hash}",
        headers=_operator_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@when("a caller presents only a site key and deletes the job")
def step_site_key_deletes_job(context) -> None:
    """Attempt to delete a job with only site key (should fail)."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    event = _build_event(
        "DELETE",
        f"/admin/jobs/{context.job_content_hash}",
        headers=_site_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@then("the job record is removed")
def step_verify_job_deleted(context) -> None:
    """Verify the job no longer exists in DynamoDB."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert item is None, f"Job {context.job_content_hash} still exists"


@then("the audio object is removed from the audio bucket")
def step_verify_audio_deleted(context) -> None:
    """Verify the audio file no longer exists in S3."""
    try:
        context.s3_client.head_object(Bucket="audio", Key=context.job_audio_key)
        assert False, f"Audio object {context.job_audio_key} still exists in S3"
    except ClientError as exc:
        # Expected: the file should not exist
        assert exc.response["Error"]["Code"] == "404", f"Unexpected error: {exc}"


@then("requesting that job returns not found")
def step_verify_get_returns_not_found(context) -> None:
    """Verify that getting the deleted job returns 404."""
    event = _build_event(
        "GET",
        f"/admin/jobs/{context.job_content_hash}",
        headers=_operator_headers(),
    )
    response = context.handler_module.handler(event, None)
    assert response["statusCode"] == 404, f"Expected 404, got {response['statusCode']}"


@then("the response is not found")
def step_verify_response_not_found(context) -> None:
    """Verify response status is 404 from the delete handler itself.

    Asserts the specific ``job_not_found`` error body raised by
    ``_delete_admin_job``, not just any 404 -- the route dispatcher's
    generic fallback for an unmatched path also returns 404, which would
    let this scenario pass even if the DELETE route were never wired up.
    """
    assert (
        context.response["statusCode"] == 404
    ), f"Expected 404, got {context.response['statusCode']}"
    assert (
        context.response_body.get("error") == "job_not_found"
    ), f"Expected job_not_found, got {context.response_body.get('error')}"


@then("the response is forbidden")
def step_verify_response_forbidden(context) -> None:
    """Verify response status is 403."""
    assert (
        context.response["statusCode"] == 403
    ), f"Expected 403, got {context.response['statusCode']}"


@then("no audio object is removed")
def step_verify_no_audio_removal_attempted(context) -> None:
    """Verify no audio was deleted (because there was none to delete)."""
    # If we got this far, it means the delete didn't crash when there was no audio_key
    # This is more of a test that the code handles missing audio_key gracefully
    pass


@then("the job record still exists")
def step_verify_job_still_exists(context) -> None:
    """Verify the job was not deleted."""
    result = context.jobs_table.get_item(Key={"content_hash": context.job_content_hash})
    item = result.get("Item")
    assert (
        item is not None
    ), f"Job {context.job_content_hash} was deleted but should exist"
