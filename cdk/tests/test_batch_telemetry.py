"""Unit tests for the batch_telemetry Lambda's timing math and correlation."""

from __future__ import annotations

import importlib
import os
import sys
from decimal import Decimal
from typing import Any

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def batch_telemetry() -> Any:
    """Provide the batch_telemetry handler module with a mocked jobs table."""
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "content_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "content_hash", "AttributeType": "S"},
                {"AttributeName": "claimed_by", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "claimed_by-index",
                    "KeySchema": [{"AttributeName": "claimed_by", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        os.environ.update(
            {
                "JOBS_TABLE": "jobs",
                "CLAIMED_BY_INDEX": "claimed_by-index",
                "WARM_START_THRESHOLD_SECONDS": "60",
                "PROVISIONING_OVERHEAD_SECONDS": "90",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )
        sys.modules.pop("handler", None)
        lambdas_dir = os.path.join(
            os.path.dirname(__file__), "..", "lambdas", "batch_telemetry"
        )
        sys.path.insert(0, lambdas_dir)
        module = importlib.import_module("handler")
        yield module
        sys.path.remove(lambdas_dir)
        sys.modules.pop("handler", None)


def test_compute_timing_cold_start_adds_provisioning_overhead(
    batch_telemetry: Any,
) -> None:
    """A startup gap over the warm-start threshold adds provisioning overhead."""
    created_at_ms = 1_700_000_000_000
    started_at_ms = created_at_ms + 120_000  # 120s gap: a cold start
    stopped_at_ms = started_at_ms + 30_000  # 30s of actual container work

    timing = batch_telemetry.compute_timing(created_at_ms, started_at_ms, stopped_at_ms)

    assert timing["container_seconds"] == 30.0
    assert timing["provisioning_seconds"] == 90.0
    assert timing["billed_seconds"] == 120.0


def test_compute_timing_warm_start_has_no_provisioning_overhead(
    batch_telemetry: Any,
) -> None:
    """A startup gap under the warm-start threshold adds no overhead."""
    created_at_ms = 1_700_000_000_000
    started_at_ms = created_at_ms + 5_000  # 5s gap: a warm start
    stopped_at_ms = started_at_ms + 45_000

    timing = batch_telemetry.compute_timing(created_at_ms, started_at_ms, stopped_at_ms)

    assert timing["container_seconds"] == 45.0
    assert timing["provisioning_seconds"] == 0.0
    assert timing["billed_seconds"] == 45.0


def test_compute_timing_handles_missing_started_and_stopped(
    batch_telemetry: Any,
) -> None:
    """A job that failed before starting a container has no container time."""
    created_at_ms = 1_700_000_000_000

    timing = batch_telemetry.compute_timing(created_at_ms, None, None)

    assert timing["container_seconds"] == 0.0
    assert timing["provisioning_seconds"] == 0.0
    assert timing["billed_seconds"] == 0.0


def test_handler_records_timing_on_matching_job(batch_telemetry: Any) -> None:
    """The handler correlates via claimed_by and writes timing fields."""
    jobs = boto3.resource("dynamodb", region_name="us-east-1").Table("jobs")
    jobs.put_item(
        Item={
            "content_hash": "abc123",
            "status": "claimed",
            "claimed_by": "batch:job-xyz",
        }
    )

    created_at_ms = 1_700_000_000_000
    event = {
        "detail": {
            "jobId": "job-xyz",
            "status": "SUCCEEDED",
            "createdAt": created_at_ms,
            "startedAt": created_at_ms + 120_000,
            "stoppedAt": created_at_ms + 150_000,
            "container": {"instanceType": "g4dn.xlarge"},
        }
    }

    result = batch_telemetry.handler(event, None)

    assert result["status"] == "recorded"
    item = jobs.get_item(Key={"content_hash": "abc123"})["Item"]
    assert item["instance_type"] == "g4dn.xlarge"
    assert item["container_seconds"] == Decimal("30")
    assert item["provisioning_seconds"] == Decimal("90")
    assert item["billed_seconds"] == Decimal("120")
    assert item["batch_created_at"].endswith("Z")
    # duration_seconds means something else (claim-to-done) and must be
    # left untouched by this handler.
    assert "duration_seconds" not in item


def test_handler_skips_cleanly_when_no_job_matches(batch_telemetry: Any) -> None:
    """An unrecognized Batch job (e.g. manual testing) does not raise."""
    event = {
        "detail": {
            "jobId": "stray-job",
            "status": "SUCCEEDED",
            "createdAt": 1_700_000_000_000,
            "startedAt": 1_700_000_010_000,
            "stoppedAt": 1_700_000_020_000,
        }
    }

    result = batch_telemetry.handler(event, None)

    assert result == {"status": "skipped", "reason": "no_matching_job"}
