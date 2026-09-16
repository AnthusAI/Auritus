"""Step definitions for daily cost rollups (by site and worker type).

These steps deliberately never call ``_create_job``/site-key flows -- job
records are seeded directly into the mocked jobs table with exactly the
fields the router/batch_telemetry code paths under test actually read
(``site_id``, ``created_at``, ``claimed_by``, ``worker_type``), matching the
convention already established in ``job_cost_estimate_steps.py``.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import boto3
from behave import given, then, when
from moto import mock_aws


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_router(context) -> None:
    """(Re)load the router handler module against the current env vars."""
    sys.modules.pop("handler", None)
    router_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "router"
    )
    sys.path.insert(0, router_path)
    router = importlib.import_module("handler")
    router._sfn = Mock()
    router._batch = Mock()
    context.router_module = router
    sys.path.remove(router_path)


def _load_batch_telemetry(context) -> None:
    """(Re)load the batch_telemetry handler module against the current env vars."""
    sys.modules.pop("handler", None)
    bt_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "batch_telemetry"
    )
    sys.path.insert(0, bt_path)
    bt = importlib.import_module("handler")
    context.batch_telemetry_module = bt
    sys.path.remove(bt_path)


def close_rollup_mock(context) -> None:
    """Exit this feature's moto mock, if one is open on ``context``.

    Called by ``features/environment.py``'s ``after_feature`` hook once
    this feature's last scenario finishes -- see ``_ensure_aws_mocks`` for
    why this must be a deterministic, feature-scoped teardown. State lives
    on ``context`` (not a module global) because behave does not load step
    files as ordinarily-importable modules under a stable ``sys.modules``
    name -- there is no reliable way for ``environment.py`` to reach back
    into this file's own module namespace, but ``context`` is the same
    single object shared by every hook and step for the whole run, so
    stashing state on it (under a leading-underscore attribute -- see
    below for why that matters) is the one channel guaranteed to work.
    """
    mock = getattr(context, "_rollup_mock_aws", None)
    if mock is not None:
        try:
            mock.__exit__(None, None, None)
        except Exception:
            pass
        context._rollup_mock_aws = None
        context._rollup_tables_ready = False

    # Also undo the os.environ pollution from _create_rollup_tables: other
    # feature files' own step modules reload the router/batch_telemetry
    # "handler" module fresh and only overwrite the env vars THEY care
    # about (JOBS_TABLE, SITES_TABLE, ...) -- they neither set nor expect
    # COST_ROLLUPS_TABLE, so a leftover value pointing at a table that
    # doesn't exist in THEIR moto mock made _mark_done/_mark_failed's new
    # rollup write raise ResourceNotFoundException for every one of them.
    # Popping it back to unset restores the router's own default ("" ->
    # rollup writing skipped entirely, exactly as it behaves when this
    # feature is simply not configured), matching real deployment
    # behavior for an environment where cost rollups aren't wired up.
    for key in (
        "COST_ROLLUPS_TABLE",
        "COST_ROLLUPS_DATE_INDEX",
        "CLAIMED_BY_INDEX",
        "WARM_START_THRESHOLD_SECONDS",
        "PROVISIONING_OVERHEAD_SECONDS",
    ):
        os.environ.pop(key, None)


def _ensure_aws_mocks(context) -> None:
    """Initialize moto mocks and DynamoDB tables for the rollup scenarios.

    Unlike ``job_cost_estimate_steps.py``'s per-scenario ``_ensure_aws_mocks``
    (which re-enters ``mock_aws()`` fresh for every scenario), this one
    enters the mock and creates its tables exactly ONCE for the whole
    ``cost_rollups.feature`` run. That state is tracked on
    ``context._rollup_mock_aws``/``context._rollup_tables_ready`` --
    leading-underscore attributes, which is deliberate: behave scopes a
    plain ``context.foo`` attribute to the current scenario's layer,
    discarding it when the scenario ends, but treats a leading-underscore
    attribute as a real instance attribute that survives across scenarios
    (and features) for the life of the run. A plain-attribute guard here
    would re-trigger ``create_table`` -- and a ``ResourceInUseException``
    -- on every single scenario.

    Re-entering ``mock_aws()`` per scenario was tried first and broke
    under the full suite (though not in isolation): behave runs every
    ``.feature`` file in one process, and moto's nested-mock accounting
    does not reliably reset a table's state when an inner mock exits while
    some other, unrelated mock elsewhere in the process is still open --
    which happens whenever this feature's scenarios interleave with any
    other file's own mock lifecycle. Entering once and reusing the same
    tables for every scenario in this file sidesteps that entirely; it's
    safe because every scenario seeds its own randomly-suffixed
    ``site_id``s and content hashes, so scenarios never collide on data
    even though they share table state.

    The single mock is closed by ``close_rollup_mock`` via
    ``features/environment.py``'s ``after_feature`` hook so it does not
    leak into feature files that run after this one alphabetically.
    """
    if getattr(context, "rollup_jobs_table", None) is not None:
        return

    if getattr(context, "_rollup_mock_aws", None) is None:
        mock = mock_aws()
        mock.__enter__()
        context._rollup_mock_aws = mock
        context._rollup_tables_ready = False

    if not getattr(context, "_rollup_tables_ready", False):
        _create_rollup_tables()
        context._rollup_tables_ready = True

    context.rollup_jobs_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table("rollup-jobs")
    context.rollup_cost_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table("rollup-cost-rollups")


def _create_rollup_tables() -> None:
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="rollup-jobs",
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
    dynamodb.create_table(
        TableName="rollup-cost-rollups",
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
    s3.create_bucket(Bucket="rollup-audio")

    os.environ.update(
        {
            "JOBS_TABLE": "rollup-jobs",
            "SITES_TABLE": "rollup-sites",
            "AUDIO_BUCKET": "rollup-audio",
            "CLOUDFRONT_DOMAIN": "audio.example.com",
            "FALLBACK_STATE_MACHINE_ARN": "",
            "FALLBACK_SECONDS": "900",
            "DAILY_SITE_QUOTA": "100",
            "BATCH_JOB_QUEUE_NAME": "",
            "GPU_HOURLY_RATE_USD": "0.526",
            "PLATFORM_COST_PER_JOB_USD": "0.0005",
            "RATE_CARD_VERSION": "v1",
            "COST_ROLLUPS_TABLE": "rollup-cost-rollups",
            "COST_ROLLUPS_DATE_INDEX": "date-site_id-index",
            "CLAIMED_BY_INDEX": "claimed_by-index",
            "WARM_START_THRESHOLD_SECONDS": "60",
            "PROVISIONING_OVERHEAD_SECONDS": "90",
            "AWS_DEFAULT_REGION": "us-east-1",
        }
    )


def _build_event(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
    path_parameters: dict[str, str] | None = None,
    query_params: dict[str, str] | None = None,
) -> dict:
    """Build an API Gateway HTTP API v2 event."""
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "headers": headers or {},
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": path_parameters,
        "queryStringParameters": query_params,
    }


def _decode(response: dict) -> dict:
    return json.loads(response["body"])


# --- Scenario: A completed Batch job adds to the daily rollup ------------


@given("the daily rollup for a site is empty")
def step_rollup_empty(context) -> None:
    _ensure_aws_mocks(context)
    context.rollup_site_id = f"site-{uuid.uuid4().hex[:8]}"
    context.rollup_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = context.rollup_cost_table.get_item(
        Key={"site_id": context.rollup_site_id, "date": context.rollup_date}
    ).get("Item")
    assert existing is None, "freshly generated site_id already has a rollup row"


@when("a Batch job for that site completes with a gpu cost")
def step_batch_job_completes(context) -> None:
    _load_batch_telemetry(context)
    content_hash = f"batch-job-{uuid.uuid4().hex[:8]}"
    batch_job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = _utc_now_iso()
    context.rollup_jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "claimed_by": f"batch:{batch_job_id}",
            "site_id": context.rollup_site_id,
            "created_at": now_iso,
        }
    )
    created_at_ms = 1_700_000_000_000
    event = {
        "detail": {
            "jobId": batch_job_id,
            "status": "SUCCEEDED",
            "createdAt": created_at_ms,
            "startedAt": created_at_ms + 5_000,  # warm start
            "stoppedAt": created_at_ms + 5_000 + 1_800_000,  # 1800s billed
            "container": {"instanceType": "g4dn.xlarge"},
        }
    }
    result = context.batch_telemetry_module.handler(event, None)
    assert result["status"] == "recorded", result

    rate = Decimal(os.environ["GPU_HOURLY_RATE_USD"])
    billed_seconds = Decimal(str(result["billed_seconds"]))
    context.rollup_expected_gpu_cost = billed_seconds * rate / Decimal(3600)
    context.rollup_date = now_iso[:10]


@then("the daily rollup gpu cost equals that job cost")
def step_gpu_cost_equals(context) -> None:
    item = context.rollup_cost_table.get_item(
        Key={"site_id": context.rollup_site_id, "date": context.rollup_date}
    )["Item"]
    assert item["gpu_cost_usd"] == context.rollup_expected_gpu_cost, (
        item["gpu_cost_usd"],
        context.rollup_expected_gpu_cost,
    )


@then("the daily rollup batch job count is one")
def step_batch_job_count_is_one(context) -> None:
    item = context.rollup_cost_table.get_item(
        Key={"site_id": context.rollup_site_id, "date": context.rollup_date}
    )["Item"]
    assert item["batch_job_count"] == Decimal(1), item["batch_job_count"]


# --- Scenario: A local job adds platform cost but no gpu cost ------------


@when("a local job for that site completes")
def step_local_job_completes(context) -> None:
    _load_router(context)
    content_hash = f"local-job-{uuid.uuid4().hex[:8]}"
    token = f"token-{content_hash}"
    now_iso = _utc_now_iso()
    context.rollup_jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Rollup test text",
            "name": "Rollup Test",
            "byline": "Tester",
            "site_key": "rollup-site-key",
            "site_id": context.rollup_site_id,
            "job_token": token,
            "claim_owner": "local:worker-1",
            "claimed_by": "local:worker-1",
            "worker_type": "local",
            "created_at": now_iso,
            "updated_at": now_iso,
            "claimed_at": now_iso,
            "claimed_at_epoch": int(time.time()),
        }
    )
    event = _build_event(
        "PUT",
        f"/jobs/{content_hash}/done",
        body={"audio_key": f"audio/{content_hash}.wav"},
        headers={"x-auritus-job-token": token},
        path_parameters={"hash": content_hash},
    )
    response = context.router_module.handler(event, None)
    assert response["statusCode"] == 200, _decode(response)
    context.rollup_date = now_iso[:10]


@then("the daily rollup gpu cost is zero")
def step_rollup_gpu_cost_is_zero(context) -> None:
    item = (
        context.rollup_cost_table.get_item(
            Key={"site_id": context.rollup_site_id, "date": context.rollup_date}
        ).get("Item")
        or {}
    )
    assert item.get("gpu_cost_usd", Decimal(0)) == Decimal(0), item.get("gpu_cost_usd")


@then("the daily rollup local job count is one")
def step_rollup_local_job_count_is_one(context) -> None:
    item = context.rollup_cost_table.get_item(
        Key={"site_id": context.rollup_site_id, "date": context.rollup_date}
    )["Item"]
    assert item["local_job_count"] == Decimal(1), item["local_job_count"]
    assert item["platform_cost_usd"] > Decimal(0), item["platform_cost_usd"]


# --- Scenario: Rollups separate sites -------------------------------------


@given('jobs complete for site "{site_a}" and site "{site_b}"')
def step_jobs_complete_for_two_sites(context, site_a: str, site_b: str) -> None:
    _ensure_aws_mocks(context)
    _load_router(context)
    context.rollup_two_sites = (
        f"{site_a}-{uuid.uuid4().hex[:6]}",
        f"{site_b}-{uuid.uuid4().hex[:6]}",
    )
    context.rollup_date = _utc_now_iso()[:10]
    for site_id in context.rollup_two_sites:
        content_hash = f"job-{site_id}-{uuid.uuid4().hex[:6]}"
        token = f"token-{content_hash}"
        now_iso = _utc_now_iso()
        context.rollup_jobs_table.put_item(
            Item={
                "content_hash": content_hash,
                "status": "claimed",
                "site_id": site_id,
                "job_token": token,
                "worker_type": "local",
                "claimed_by": "local:worker-1",
                "created_at": now_iso,
                "claimed_at": now_iso,
                "claimed_at_epoch": int(time.time()),
            }
        )
        event = _build_event(
            "PUT",
            f"/jobs/{content_hash}/done",
            body={"audio_key": f"audio/{content_hash}.wav"},
            headers={"x-auritus-job-token": token},
            path_parameters={"hash": content_hash},
        )
        response = context.router_module.handler(event, None)
        assert response["statusCode"] == 200, _decode(response)


@then("each site has its own daily rollup")
def step_each_site_has_own_rollup(context) -> None:
    site_a, site_b = context.rollup_two_sites
    item_a = context.rollup_cost_table.get_item(
        Key={"site_id": site_a, "date": context.rollup_date}
    ).get("Item")
    item_b = context.rollup_cost_table.get_item(
        Key={"site_id": site_b, "date": context.rollup_date}
    ).get("Item")
    assert item_a is not None, f"no rollup row for {site_a}"
    assert item_b is not None, f"no rollup row for {site_b}"
    assert item_a["local_job_count"] == Decimal(1)
    assert item_b["local_job_count"] == Decimal(1)
    assert item_a["site_id"] != item_b["site_id"]


# --- Scenario: A retried rollup write does not double count ---------------


@given("a job has already been rolled up with a gpu cost")
def step_job_already_rolled_up(context) -> None:
    _ensure_aws_mocks(context)
    _load_batch_telemetry(context)
    context.retry_site_id = f"site-retry-{uuid.uuid4().hex[:8]}"
    context.retry_batch_job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = _utc_now_iso()
    context.rollup_jobs_table.put_item(
        Item={
            "content_hash": f"job-retry-{uuid.uuid4().hex[:8]}",
            "status": "claimed",
            "claimed_by": f"batch:{context.retry_batch_job_id}",
            "site_id": context.retry_site_id,
            "created_at": now_iso,
        }
    )
    created_at_ms = 1_700_000_000_000
    context.retry_event = {
        "detail": {
            "jobId": context.retry_batch_job_id,
            "status": "SUCCEEDED",
            "createdAt": created_at_ms,
            "startedAt": created_at_ms + 5_000,
            "stoppedAt": created_at_ms + 5_000 + 3_600_000,
            "container": {"instanceType": "g4dn.xlarge"},
        }
    }
    # First delivery: this is the real write the retry must not duplicate.
    first_result = context.batch_telemetry_module.handler(
        json.loads(json.dumps(context.retry_event)), None
    )
    assert first_result["status"] == "recorded", first_result
    context.retry_date = now_iso[:10]

    item = context.rollup_cost_table.get_item(
        Key={"site_id": context.retry_site_id, "date": context.retry_date}
    )["Item"]
    context.retry_gpu_cost_after_first = item["gpu_cost_usd"]
    assert context.retry_gpu_cost_after_first > Decimal(0)


@when("the same job's rollup write is attempted again")
def step_retry_rollup_write(context) -> None:
    # A genuine EventBridge at-least-once redelivery: the same handler,
    # invoked again with an independently-deserialized copy of the exact
    # same event -- not a different call shape, not mark_done called twice
    # with different job states. This IS what a redelivery looks like.
    second_result = context.batch_telemetry_module.handler(
        json.loads(json.dumps(context.retry_event)), None
    )
    assert second_result["status"] == "recorded", second_result


@then("the daily rollup gpu cost is unchanged")
def step_rollup_gpu_cost_unchanged(context) -> None:
    item = context.rollup_cost_table.get_item(
        Key={"site_id": context.retry_site_id, "date": context.retry_date}
    )["Item"]
    assert item["gpu_cost_usd"] == context.retry_gpu_cost_after_first, (
        item["gpu_cost_usd"],
        context.retry_gpu_cost_after_first,
    )
    # Prove the whole contribution was suppressed, not just the cost figure.
    assert item["batch_job_count"] == Decimal(1), item["batch_job_count"]


# --- Scenario: Rollups are read without scanning the jobs table ----------


@given("thirty days of rollups exist for a site")
def step_thirty_days_of_rollups(context) -> None:
    _ensure_aws_mocks(context)
    _load_router(context)
    context.scan_site_id = f"site-scan-{uuid.uuid4().hex[:8]}"
    base = datetime.now(timezone.utc).date()
    context.scan_seed_total_gpu = Decimal(0)
    context.scan_seed_total_platform = Decimal(0)
    seed_days = []
    for i in range(30):
        day = (base - timedelta(days=i)).strftime("%Y-%m-%d")
        gpu = Decimal("0.10") + Decimal(i) / Decimal(100)
        platform = Decimal("0.01")
        context.rollup_cost_table.put_item(
            Item={
                "site_id": context.scan_site_id,
                "date": day,
                "gpu_cost_usd": gpu,
                "platform_cost_usd": platform,
                "batch_job_count": 1,
                "local_job_count": 0,
                "billed_seconds": Decimal(600),
                "local_duration_seconds": Decimal(0),
            }
        )
        context.scan_seed_total_gpu += gpu
        context.scan_seed_total_platform += platform
        seed_days.append(day)
    context.scan_from = min(seed_days)
    context.scan_to = max(seed_days)


@when("the operator requests the cost summary for that site")
def step_request_cost_summary(context) -> None:
    # Prove this route never falls back to scanning the jobs table: any
    # Scan call on _jobs raises immediately.
    context.router_module._jobs.scan = Mock(
        side_effect=AssertionError("must not scan the jobs table")
    )
    event = _build_event(
        "GET",
        "/admin/costs",
        headers={"authorization": "Bearer operator-token"},
        query_params={
            "site_id": context.scan_site_id,
            "from": context.scan_from,
            "to": context.scan_to,
        },
    )
    context.scan_response = context.router_module.handler(event, None)
    context.scan_body = _decode(context.scan_response)


@then("the summary reflects exactly the rollup records")
def step_summary_matches_rollups(context) -> None:
    assert context.scan_response["statusCode"] == 200, context.scan_body
    daily = context.scan_body["daily"]
    assert len(daily) == 30, len(daily)
    total = context.scan_body["total"]
    assert abs(total["gpu_cost_usd"] - float(context.scan_seed_total_gpu)) < 1e-9
    assert (
        abs(total["platform_cost_usd"] - float(context.scan_seed_total_platform)) < 1e-9
    )
    assert total["batch_job_count"] == 30, total["batch_job_count"]
