"""Step definitions for the per-job cost estimate (GPU + platform cost)."""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import boto3
from behave import given, then
from moto import mock_aws


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
                "GPU_HOURLY_RATE_USD": "0.526",
                "PLATFORM_COST_PER_JOB_USD": "0.0005",
                "RATE_CARD_VERSION": "v1",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )

        sites = boto3.resource("dynamodb", region_name="us-east-1").Table("sites")
        sites.put_item(
            Item={
                "site_id": "site-cost-estimate",
                "site_key": "test-key-cost-estimate",
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
    return json.loads(response["body"])


def _create_claimed_local_job(context, content_hash: str) -> None:
    now = _utc_now_iso()
    context.jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Cost estimate test text",
            "name": "Cost Test Job",
            "byline": "Test Author",
            "site_key": "test-key-cost-estimate",
            "site_id": "site-cost-estimate",
            "job_token": "test-token-cost-estimate",
            "claim_owner": "local:test-worker",
            "claimed_by": "local:test-worker",
            "worker_type": "local",
            "created_at": now,
            "updated_at": now,
            "claimed_at": now,
            "claimed_at_epoch": int(time.time()),
        }
    )


@given("a local job is marked done")
def step_local_job_marked_done(context) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.cost_job_hash = "test-job-hash-cost-done-001"
    _create_claimed_local_job(context, context.cost_job_hash)

    event = _build_event(
        "PUT",
        f"/jobs/{context.cost_job_hash}/done",
        body={"audio_key": f"audio/{context.cost_job_hash}.wav"},
        headers={"x-auritus-job-token": "test-token-cost-estimate"},
        path_parameters={"hash": context.cost_job_hash},
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)
    assert (
        context.response["statusCode"] == 200
    ), f"Expected 200, got {context.response['statusCode']}: {context.response_body}"

    context.cost_job_item = context.jobs_table.get_item(
        Key={"content_hash": context.cost_job_hash}
    )["Item"]


@given("a local job is marked failed")
def step_local_job_marked_failed(context) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)

    context.cost_job_hash = "test-job-hash-cost-failed-001"
    _create_claimed_local_job(context, context.cost_job_hash)

    event = _build_event(
        "PUT",
        f"/jobs/{context.cost_job_hash}/failed",
        body={"reason": "synthesis_error", "owner": "local:test-worker"},
        headers={"x-auritus-job-token": "test-token-cost-estimate"},
        path_parameters={"hash": context.cost_job_hash},
    )
    context.response = context.handler_module.handler(event, None)
    context.response_body = _decode_response_body(context.response)
    assert (
        context.response["statusCode"] == 200
    ), f"Expected 200, got {context.response['statusCode']}: {context.response_body}"

    context.cost_job_item = context.jobs_table.get_item(
        Key={"content_hash": context.cost_job_hash}
    )["Item"]


@then("the job gpu cost is zero")
def step_gpu_cost_is_zero(context) -> None:
    item = context.cost_job_item
    assert "gpu_cost_usd" in item, "gpu_cost_usd was not written to the job record"
    assert item["gpu_cost_usd"] == Decimal(
        0
    ), f"Expected gpu_cost_usd == 0, got {item['gpu_cost_usd']}"


@then("the job platform cost is greater than zero")
def step_platform_cost_is_greater_than_zero(context) -> None:
    item = context.cost_job_item
    assert (
        "platform_cost_usd" in item
    ), "platform_cost_usd was not written to the job record"
    assert item["platform_cost_usd"] > Decimal(
        0
    ), f"Expected platform_cost_usd > 0, got {item['platform_cost_usd']}"


@then("the job records a cost rate and a rate card version")
def step_records_cost_rate_and_version(context) -> None:
    item = context.cost_job_item
    assert (
        "cost_rate_usd_per_hour" in item
    ), "cost_rate_usd_per_hour was not written to the job record"
    assert item["cost_rate_usd_per_hour"] > Decimal(
        0
    ), f"Expected cost_rate_usd_per_hour > 0, got {item['cost_rate_usd_per_hour']}"
    assert item.get(
        "rate_card_version"
    ), "rate_card_version was not written to the job record"
