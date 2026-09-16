"""Unit tests for the cost_reconciliation Lambda's estimate-vs-actual logic.

moto's Cost Explorer support (``ce.get_cost_and_usage``) always returns an
empty ``ResultsByTime`` regardless of input -- it does not simulate real
billing data -- so real actual-cost figures are injected here by replacing
``handler._ce`` with a ``Mock``, the same pattern ``cdk/tests/conftest.py``
uses for ``_sfn``/``_batch`` on the router handler.
"""

from __future__ import annotations

import importlib
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import Mock

import boto3
import pytest
from moto import mock_aws


def _ce_response(amount: str) -> dict[str, Any]:
    return {
        "ResultsByTime": [
            {"Total": {"UnblendedCost": {"Amount": amount, "Unit": "USD"}}}
        ]
    }


@pytest.fixture
def cost_reconciliation() -> Any:
    """Provide the cost_reconciliation handler module with a mocked rollups table."""
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
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
        os.environ.update(
            {
                "COST_ROLLUPS_TABLE": "cost_rollups",
                "COST_ROLLUPS_DATE_INDEX": "date-site_id-index",
                "variance_threshold_percent": "20",
                "RECONCILIATION_LOOKBACK_DAYS": "7",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )
        sys.modules.pop("handler", None)
        lambdas_dir = os.path.join(
            os.path.dirname(__file__), "..", "lambdas", "cost_reconciliation"
        )
        sys.path.insert(0, lambdas_dir)
        module = importlib.import_module("handler")
        module._ce = Mock()
        try:
            yield module
        finally:
            sys.path.remove(lambdas_dir)
            sys.modules.pop("handler", None)
            for key in (
                "COST_ROLLUPS_TABLE",
                "COST_ROLLUPS_DATE_INDEX",
                "variance_threshold_percent",
                "RECONCILIATION_LOOKBACK_DAYS",
            ):
                os.environ.pop(key, None)


def _rollups_table() -> Any:
    return boto3.resource("dynamodb", region_name="us-east-1").Table("cost_rollups")


def test_reconciles_day_with_existing_per_site_rollups(
    cost_reconciliation: Any,
) -> None:
    """A day with per-site GPU cost rollups gets an __account__ row with actual/variance."""
    rollups = _rollups_table()
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-10",
            "gpu_cost_usd": Decimal("1.00"),
        }
    )
    rollups.put_item(
        Item={
            "site_id": "site-b",
            "date": "2026-09-10",
            "gpu_cost_usd": Decimal("2.00"),
        }
    )
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("3.30")

    now = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
    result = cost_reconciliation._reconcile_date("2026-09-10")

    assert result["estimated_gpu_cost_usd"] == "3.00"
    assert result["actual_cost_usd"] == "3.30"
    assert result["variance_usd"] == "0.30"

    row = rollups.get_item(Key={"site_id": "__account__", "date": "2026-09-10"})["Item"]
    assert row["actual_cost_usd"] == Decimal("3.30")
    assert row["estimated_gpu_cost_usd"] == Decimal("3.00")
    assert row["variance_usd"] == Decimal("0.30")
    assert row["reconciled_at"].endswith("Z")
    # Within the default 20% tolerance: 0.30 / 3.00 == 10%.
    assert row["out_of_tolerance"] is False
    del now  # only used for readability of intent above


def test_day_closed_less_than_24h_ago_is_not_reconciled(
    cost_reconciliation: Any,
) -> None:
    """A day still inside the 24h finality window is excluded from the pending set."""
    now = datetime(2026, 9, 16, 0, 30, tzinfo=timezone.utc)

    dates = cost_reconciliation._dates_to_reconcile(now)

    # At 00:30 UTC on the 16th, 2026-09-15 closed at 2026-09-16T00:00Z --
    # only 30 minutes ago, well under 24h -- so the most recent eligible
    # day is 2026-09-14, not 2026-09-15.
    assert "2026-09-15" not in dates
    assert "2026-09-14" in dates


def test_reconciliation_is_idempotent_on_rerun(cost_reconciliation: Any) -> None:
    """Running reconciliation twice for the same day yields identical stored values."""
    rollups = _rollups_table()
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-10",
            "gpu_cost_usd": Decimal("1.00"),
        }
    )
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("1.00")

    cost_reconciliation._reconcile_date("2026-09-10")
    first = rollups.get_item(Key={"site_id": "__account__", "date": "2026-09-10"})[
        "Item"
    ]

    cost_reconciliation._reconcile_date("2026-09-10")
    second = rollups.get_item(Key={"site_id": "__account__", "date": "2026-09-10"})[
        "Item"
    ]

    # A SET write reproduces the same figures verbatim -- not doubled, the
    # way an ADD-based accumulator would double a re-applied contribution.
    assert first["actual_cost_usd"] == second["actual_cost_usd"] == Decimal("1.00")
    assert (
        first["estimated_gpu_cost_usd"]
        == second["estimated_gpu_cost_usd"]
        == Decimal("1.00")
    )
    assert first["variance_usd"] == second["variance_usd"] == Decimal("0")


def test_variance_exceeding_threshold_is_out_of_tolerance(
    cost_reconciliation: Any,
) -> None:
    """A variance beyond variance_threshold_percent sets out_of_tolerance true."""
    rollups = _rollups_table()
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-11",
            "gpu_cost_usd": Decimal("10.00"),
        }
    )
    # 30% variance, over the default 20% threshold.
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("13.00")

    cost_reconciliation._reconcile_date("2026-09-11")

    row = rollups.get_item(Key={"site_id": "__account__", "date": "2026-09-11"})["Item"]
    assert row["out_of_tolerance"] is True


def test_variance_within_threshold_is_not_out_of_tolerance(
    cost_reconciliation: Any,
) -> None:
    """A variance within variance_threshold_percent leaves out_of_tolerance false."""
    rollups = _rollups_table()
    rollups.put_item(
        Item={
            "site_id": "site-a",
            "date": "2026-09-12",
            "gpu_cost_usd": Decimal("10.00"),
        }
    )
    # 5% variance, under the default 20% threshold.
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("10.50")

    cost_reconciliation._reconcile_date("2026-09-12")

    row = rollups.get_item(Key={"site_id": "__account__", "date": "2026-09-12"})["Item"]
    assert row["out_of_tolerance"] is False


def test_zero_estimate_with_nonzero_actual_is_out_of_tolerance(
    cost_reconciliation: Any,
) -> None:
    """A zero estimate against nonzero actual cost is flagged, not silently skipped.

    No per-site rollup rows exist for this date at all (estimated GPU cost
    sums to zero), yet Cost Explorer reports real spend -- a sign the
    estimate pipeline missed something, which is itself worth flagging
    rather than treated as an undefined/skipped case.
    """
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("0.50")

    result = cost_reconciliation._reconcile_date("2026-09-13")

    assert result["estimated_gpu_cost_usd"] == "0"
    assert result["out_of_tolerance"] is True


def test_zero_estimate_with_zero_actual_is_within_tolerance(
    cost_reconciliation: Any,
) -> None:
    """A zero estimate against zero actual cost is perfect agreement, not an error."""
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("0")

    result = cost_reconciliation._reconcile_date("2026-09-14")

    assert result["estimated_gpu_cost_usd"] == "0"
    assert result["out_of_tolerance"] is False


def test_handler_reconciles_all_pending_dates_in_lookback_window(
    cost_reconciliation: Any,
) -> None:
    """The handler reconciles every unreconciled final day, not just one."""
    cost_reconciliation._ce.get_cost_and_usage.return_value = _ce_response("1.00")

    # Freeze "now" by monkeypatching datetime.now via the module's own
    # dependency: _dates_to_reconcile takes `now` as an argument, but
    # handler() computes it internally, so exercise handler() directly and
    # just assert on shape/idempotency rather than the exact calendar dates
    # (those are covered precisely by test_dates_to_reconcile-style tests
    # above).
    result = cost_reconciliation.handler({}, None)
    assert isinstance(result["reconciled"], list)
    assert len(result["reconciled"]) == cost_reconciliation.RECONCILIATION_LOOKBACK_DAYS

    # Re-running immediately finds nothing left pending -- every date in
    # the window now has reconciled_at set.
    second = cost_reconciliation.handler({}, None)
    assert second["reconciled"] == []
