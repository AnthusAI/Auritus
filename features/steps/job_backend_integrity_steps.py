"""Step definitions for job backend integrity on content hash collision."""

from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import Mock

import boto3
from behave import given, then, when
from moto import mock_aws


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _site_headers() -> dict[str, str]:
    """Return valid site-key and origin headers."""
    return {"x-auritus-site-key": "test-key-integrity", "origin": "https://example.com"}


def _ensure_handler_loaded(context) -> None:
    """Load the router handler module if not already loaded."""
    if not hasattr(context, "_handler_loaded"):
        # Remove any cached module
        sys.modules.pop("handler", None)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "router"))
        handler = importlib.import_module("handler")
        # Mock external AWS service calls
        handler._sfn = Mock()
        handler._batch = Mock()
        context.handler_module = handler
        context._handler_loaded = True


def _ensure_aws_mocks(context) -> None:
    """Initialize moto mocks and DynamoDB tables if not already done."""
    if not hasattr(context, "_aws_mocks_initialized"):
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
        os.environ.update({
            "JOBS_TABLE": "jobs",
            "SITES_TABLE": "sites",
            "AUDIO_BUCKET": "audio",
            "CLOUDFRONT_DOMAIN": "audio.example.com",
            "FALLBACK_STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:fallback",
            "FALLBACK_SECONDS": "900",
            "DAILY_SITE_QUOTA": "100",
            "BATCH_JOB_QUEUE_NAME": "test-queue",
            "AWS_DEFAULT_REGION": "us-east-1",
        })

        # Create sites table and insert test site
        sites = boto3.resource("dynamodb", region_name="us-east-1").Table("sites")
        sites.put_item(
            Item={
                "site_id": "site-integrity",
                "site_key": "test-key-integrity",
                "origin": "https://example.com",
                "allowed_origins": ["https://example.com"],
                "daily_quota": 100,
                "disabled": False,
            }
        )

        context.jobs_table = boto3.resource("dynamodb", region_name="us-east-1").Table("jobs")
        context.sites_table = sites
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


@given('a job exists with backend "{backend}", status "{status}", and stored audio')
def step_create_existing_job(context, backend: str, status: str) -> None:
    """Create an existing job with a specific backend and status."""
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.existing_content_hash = "test-collision-hash-abc123xyz"
    context.existing_backend = backend
    context.existing_audio_key = f"audio/{context.existing_content_hash}.wav"

    # Directly insert a job into the jobs table
    context.jobs_table.put_item(
        Item={
            "content_hash": context.existing_content_hash,
            "status": status,
            "tts_backend": backend,
            "voice_id": "af_heart",
            "text": "Original text",
            "name": "Original",
            "byline": "Original Author",
            "site_key": "test-key-integrity",
            "site_id": "site-integrity",
            "job_token": "original-token-12345",
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "audio_key": context.existing_audio_key,
        }
    )


@when('a job is created with that explicit content hash and backend "{new_backend}"')
def step_create_job_with_collision(context, new_backend: str) -> None:
    """Attempt to create a job with the same content hash but different backend."""
    event = _build_event(
        "POST",
        "/jobs",
        body={
            "text": "Different text",
            "tts_backend": new_backend,
            "voice_id": "af_heart",
            "content_hash": context.existing_content_hash,  # Use the existing hash
            "name": "New",
            "byline": "New Author",
        },
        headers=_site_headers(),
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)


@then("the stored job still has backend \"{expected_backend}\"")
def step_verify_backend_unchanged(context, expected_backend: str) -> None:
    """Verify that the job's backend was not changed."""
    item = context.jobs_table.get_item(Key={"content_hash": context.existing_content_hash}).get("Item")
    assert item is not None, f"Job with hash {context.existing_content_hash} not found"
    actual_backend = item.get("tts_backend")
    assert (
        actual_backend == expected_backend
    ), f"Expected backend {expected_backend}, got {actual_backend}"


@then("the stored job still points at the original audio")
def step_verify_audio_unchanged(context) -> None:
    """Verify that the job's audio_key still points to the original audio."""
    item = context.jobs_table.get_item(Key={"content_hash": context.existing_content_hash}).get("Item")
    assert item is not None, f"Job with hash {context.existing_content_hash} not found"
    actual_audio_key = item.get("audio_key")
    assert (
        actual_audio_key == context.existing_audio_key
    ), f"Expected audio_key {context.existing_audio_key}, got {actual_audio_key}"
