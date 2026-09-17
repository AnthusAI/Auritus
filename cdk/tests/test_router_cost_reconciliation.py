"""Router tests for the __account__ reconciliation row surfaced by /admin/costs.

Uses its own fixture (rather than the shared ``router_resources`` fixture in
``conftest.py``) because the reconciliation feature needs a cost_rollups
table with the ``date-site_id-index`` GSI, which the shared fixture does not
create -- no prior router test exercised ``_get_admin_costs`` at all.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def cost_router_resources() -> Any:
    """Provide a router handler with jobs/sites/cost_rollups tables mocked."""
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "content_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "content_hash", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="sites",
            KeySchema=[{"AttributeName": "site_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "site_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="cost_rollups",
            KeySchema=[
                {"AttributeName": "site_id", "KeyType": "HASH"},
                {"AttributeName": "date", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "site_id", "AttributeType": "S"},
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "date-site_id-index",
                    "KeySchema": [
                        {"AttributeName": "date", "KeyType": "HASH"},
                        {"AttributeName": "site_id", "KeyType": "RANGE"},
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
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="audio")
        os.environ.update(
            {
                "JOBS_TABLE": "jobs",
                "SITES_TABLE": "sites",
                "AUDIO_BUCKET": "audio",
                "CLOUDFRONT_DOMAIN": "audio.example.com",
                "FALLBACK_SECONDS": "900",
                "DAILY_SITE_QUOTA": "100",
                "COST_ROLLUPS_TABLE": "cost_rollups",
                "COST_ROLLUPS_DATE_INDEX": "date-site_id-index",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )
        sys.modules.pop("handler", None)
        lambdas_dir = os.path.join(os.path.dirname(__file__), "..", "lambdas", "router")
        sys.path.insert(0, lambdas_dir)
        handler = importlib.import_module("handler")
        handler._sfn = Mock()
        handler._batch = Mock()

        def event(
            method: str,
            path: str,
            *,
            body: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None,
            query_string_parameters: dict[str, str] | None = None,
        ) -> dict[str, Any]:
            return {
                "requestContext": {"http": {"method": method}},
                "rawPath": path,
                "headers": headers or {},
                "body": json.dumps(body) if body is not None else None,
                "pathParameters": None,
                "queryStringParameters": query_string_parameters,
            }

        def response_body(response: dict[str, Any]) -> dict[str, Any]:
            return json.loads(response["body"])

        yield {
            "handler": handler,
            "cost_rollups": boto3.resource("dynamodb", region_name="us-east-1").Table(
                "cost_rollups"
            ),
            "event": event,
            "response_body": response_body,
        }
        sys.path.remove(lambdas_dir)
        sys.modules.pop("handler", None)
        for key in ("COST_ROLLUPS_TABLE", "COST_ROLLUPS_DATE_INDEX"):
            os.environ.pop(key, None)


def _operator_headers() -> dict[str, str]:
    return {"authorization": "Bearer test-operator-token"}


def test_admin_costs_surfaces_account_reconciliation_row(
    cost_router_resources: Any,
) -> None:
    """The __account__ sentinel row appears under `reconciliation`, not `daily`."""
    rollups = cost_router_resources["cost_rollups"]
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-10",
            "gpu_cost_usd": Decimal("1.00"),
            "platform_cost_usd": Decimal("0.01"),
        }
    )
    rollups.put_item(
        Item={
            "site_id": "__account__",
            "date": "2026-09-10",
            "actual_cost_usd": Decimal("1.30"),
            "estimated_gpu_cost_usd": Decimal("1.00"),
            "variance_usd": Decimal("0.30"),
            "reconciled_at": "2026-09-11T06:00:00Z",
            "out_of_tolerance": False,
        }
    )

    handler = cost_router_resources["handler"]
    event = cost_router_resources["event"](
        "GET",
        "/admin/costs",
        headers=_operator_headers(),
        query_string_parameters={"from": "2026-09-10", "to": "2026-09-10"},
    )
    response = handler.handler(event, None)
    body = cost_router_resources["response_body"](response)

    assert response["statusCode"] == 200
    # The real site's row is in `daily`; the sentinel is NOT.
    assert len(body["daily"]) == 1
    assert body["daily"][0]["site_id"] == "site-a"
    assert all(row["site_id"] != "__account__" for row in body["daily"])

    # `total` sums only real per-site rows -- unaffected by the sentinel.
    assert body["total"]["gpu_cost_usd"] == 1.0

    # The sentinel surfaces separately, under `reconciliation`.
    assert len(body["reconciliation"]) == 1
    recon_row = body["reconciliation"][0]
    assert recon_row["date"] == "2026-09-10"
    assert recon_row["actual_cost_usd"] == 1.3
    assert recon_row["variance_usd"] == 0.3
    assert recon_row["out_of_tolerance"] is False


def test_admin_costs_reconciliation_empty_when_no_sentinel_row(
    cost_router_resources: Any,
) -> None:
    """No __account__ row for the range means an empty `reconciliation` list."""
    rollups = cost_router_resources["cost_rollups"]
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-12",
            "gpu_cost_usd": Decimal("1.00"),
        }
    )

    handler = cost_router_resources["handler"]
    event = cost_router_resources["event"](
        "GET",
        "/admin/costs",
        headers=_operator_headers(),
        query_string_parameters={"from": "2026-09-12", "to": "2026-09-12"},
    )
    response = handler.handler(event, None)
    body = cost_router_resources["response_body"](response)

    assert body["reconciliation"] == []


def test_admin_costs_site_scoped_query_has_no_reconciliation_key_populated(
    cost_router_resources: Any,
) -> None:
    """A site-scoped query never surfaces the account-wide sentinel row.

    Cost Explorer cannot attribute actual spend to one site, so a
    site-scoped query has nothing meaningful to report here -- the
    per-site KeyConditionExpression path never even queries the
    __account__ partition.
    """
    rollups = cost_router_resources["cost_rollups"]
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-13",
            "gpu_cost_usd": Decimal("1.00"),
        }
    )
    rollups.put_item(
        Item={
            "site_id": "__account__",
            "date": "2026-09-13",
            "actual_cost_usd": Decimal("1.30"),
            "reconciled_at": "2026-09-14T06:00:00Z",
        }
    )

    handler = cost_router_resources["handler"]
    event = cost_router_resources["event"](
        "GET",
        "/admin/costs",
        headers=_operator_headers(),
        query_string_parameters={
            "site_id": "site-a",
            "from": "2026-09-13",
            "to": "2026-09-13",
        },
    )
    response = handler.handler(event, None)
    body = cost_router_resources["response_body"](response)

    assert body["reconciliation"] == []
    assert len(body["daily"]) == 1


def test_admin_costs_backfills_missing_fields_on_sparse_rollup_rows(
    cost_router_resources: Any,
) -> None:
    """A rollup row is written incrementally per field (_record_rollup_contribution
    only ADDs the fields the completing job's path touches), so a local-only
    day has no gpu_cost_usd/batch_job_count/billed_seconds key at all, and a
    Batch-only day has no local_job_count/local_duration_seconds key. Every
    consumer (CLI, console) expects a complete row -- the console's daily
    table crashed rendering `day.local_duration_seconds.toFixed(...)` against
    a real Batch-only production row missing that key entirely. Every field
    in _COST_TOTAL_FIELDS must be present (defaulted to 0) on every row.
    """
    rollups = cost_router_resources["cost_rollups"]
    # Batch-only day: no local_job_count / local_duration_seconds key at all.
    rollups.put_item(
        Item={
            "site_id": "site-batch-only",
            "date": "2026-09-17",
            "gpu_cost_usd": Decimal("0.01"),
            "platform_cost_usd": Decimal("0.0005"),
            "batch_job_count": Decimal("1"),
            "billed_seconds": Decimal("42"),
            "avoided_cost_usd": Decimal("0"),
        }
    )
    # Local-only day: no gpu_cost_usd / batch_job_count / billed_seconds key.
    rollups.put_item(
        Item={
            "site_id": "site-local-only",
            "date": "2026-09-17",
            "platform_cost_usd": Decimal("0.0005"),
            "local_job_count": Decimal("1"),
            "local_duration_seconds": Decimal("13"),
            "avoided_cost_usd": Decimal("0.0019"),
        }
    )

    handler = cost_router_resources["handler"]
    event = cost_router_resources["event"](
        "GET",
        "/admin/costs",
        headers=_operator_headers(),
        query_string_parameters={"from": "2026-09-17", "to": "2026-09-17"},
    )
    response = handler.handler(event, None)
    body = cost_router_resources["response_body"](response)

    assert response["statusCode"] == 200
    daily_by_site = {row["site_id"]: row for row in body["daily"]}

    batch_only = daily_by_site["site-batch-only"]
    assert batch_only["local_job_count"] == 0
    assert batch_only["local_duration_seconds"] == 0

    local_only = daily_by_site["site-local-only"]
    assert local_only["gpu_cost_usd"] == 0
    assert local_only["batch_job_count"] == 0
    assert local_only["billed_seconds"] == 0

    # Every row must carry every field in _COST_TOTAL_FIELDS, not just the
    # ones its own write path happened to ADD.
    for row in body["daily"]:
        for field in handler._COST_TOTAL_FIELDS:
            assert field in row
