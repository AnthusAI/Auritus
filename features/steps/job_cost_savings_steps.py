"""Step definitions for local-job avoided-cost savings.

Follows the same feature-scoped moto mock convention established in
``cost_rollups_steps.py`` (one ``mock_aws()`` entered and one set of tables
created for the whole feature run, torn down by ``close_savings_mock`` via
``features/environment.py``'s ``after_feature`` hook) rather than the
per-scenario style used elsewhere, for the identical reason: this feature's
scenarios interleave with other files' own mock lifecycles under the full
suite, and moto's nested-mock accounting does not reliably survive that
when mocks are entered and exited per scenario.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
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


def close_savings_mock(context) -> None:
    """Exit this feature's moto mock, if one is open on ``context``.

    See ``cost_rollups_steps.close_rollup_mock`` for the full rationale --
    this is the same pattern applied to this feature's own tables/env vars.
    """
    mock = getattr(context, "_savings_mock_aws", None)
    if mock is not None:
        try:
            mock.__exit__(None, None, None)
        except Exception:
            pass
        context._savings_mock_aws = None
        context._savings_tables_ready = False

    for key in (
        "COST_ROLLUPS_TABLE",
        "COST_ROLLUPS_DATE_INDEX",
        "BACKEND_TIMING_TABLE",
        "CLAIMED_BY_INDEX",
        "WARM_START_THRESHOLD_SECONDS",
        "PROVISIONING_OVERHEAD_SECONDS",
    ):
        os.environ.pop(key, None)


def _ensure_aws_mocks(context) -> None:
    """Initialize moto mocks and DynamoDB tables for the savings scenarios.

    Entered once for the whole ``job_cost_savings.feature`` run -- see this
    module's docstring and ``cost_rollups_steps._ensure_aws_mocks`` for why.
    """
    if getattr(context, "savings_jobs_table", None) is not None:
        return

    if getattr(context, "_savings_mock_aws", None) is None:
        mock = mock_aws()
        mock.__enter__()
        context._savings_mock_aws = mock
        context._savings_tables_ready = False

    if not getattr(context, "_savings_tables_ready", False):
        _create_savings_tables()
        context._savings_tables_ready = True

    context.savings_jobs_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table("savings-jobs")
    context.savings_cost_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table("savings-cost-rollups")
    context.savings_backend_timing_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table("savings-backend-timing")


def _create_savings_tables() -> None:
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="savings-jobs",
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
        TableName="savings-cost-rollups",
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
    dynamodb.create_table(
        TableName="savings-backend-timing",
        KeySchema=[{"AttributeName": "tts_backend", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "tts_backend", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="savings-audio")

    os.environ.update(
        {
            "JOBS_TABLE": "savings-jobs",
            "SITES_TABLE": "savings-sites",
            "AUDIO_BUCKET": "savings-audio",
            "CLOUDFRONT_DOMAIN": "audio.example.com",
            "FALLBACK_STATE_MACHINE_ARN": "",
            "FALLBACK_SECONDS": "900",
            "DAILY_SITE_QUOTA": "100",
            "BATCH_JOB_QUEUE_NAME": "",
            "GPU_HOURLY_RATE_USD": "0.526",
            "PLATFORM_COST_PER_JOB_USD": "0.0005",
            "RATE_CARD_VERSION": "v1",
            "COST_ROLLUPS_TABLE": "savings-cost-rollups",
            "COST_ROLLUPS_DATE_INDEX": "date-site_id-index",
            "BACKEND_TIMING_TABLE": "savings-backend-timing",
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


def _put_local_job(
    context, *, content_hash: str, tts_backend: str, site_id: str
) -> str:
    token = f"token-{content_hash}"
    now_iso = _utc_now_iso()
    context.savings_jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "tts_backend": tts_backend,
            "voice_id": "af_heart",
            "text": "Savings test text",
            "name": "Savings Test",
            "byline": "Tester",
            "site_key": "savings-site-key",
            "site_id": site_id,
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
    return token


def _mark_done(context, content_hash: str, token: str) -> dict:
    event = _build_event(
        "PUT",
        f"/jobs/{content_hash}/done",
        body={"audio_key": f"audio/{content_hash}.wav"},
        headers={"x-auritus-job-token": token},
        path_parameters={"hash": content_hash},
    )
    response = context.router_module.handler(event, None)
    assert response["statusCode"] == 200, _decode(response)
    return _decode(response)


# --- Scenario: falls back to local duration when no Batch average exists --


@given("no Batch samples exist for a backend")
def step_no_batch_samples(context) -> None:
    _ensure_aws_mocks(context)
    context.savings_backend = f"backend-{uuid.uuid4().hex[:8]}"
    existing = context.savings_backend_timing_table.get_item(
        Key={"tts_backend": context.savings_backend}
    ).get("Item")
    assert existing is None, "freshly generated backend already has timing data"


@when("a local job using that backend completes")
def step_local_job_using_backend_completes(context) -> None:
    _load_router(context)
    context.savings_site_id = f"site-{uuid.uuid4().hex[:8]}"
    content_hash = f"local-job-{uuid.uuid4().hex[:8]}"
    token = _put_local_job(
        context,
        content_hash=content_hash,
        tts_backend=context.savings_backend,
        site_id=context.savings_site_id,
    )
    context.savings_content_hash = content_hash
    _mark_done(context, content_hash, token)
    context.savings_job_item = context.savings_jobs_table.get_item(
        Key={"content_hash": content_hash}
    )["Item"]


@then("the job avoided cost is based on its own duration")
def step_avoided_cost_based_on_duration(context) -> None:
    item = context.savings_job_item
    rate = Decimal(os.environ["GPU_HOURLY_RATE_USD"])
    duration = item["duration_seconds"]
    expected = Decimal(duration) * rate / Decimal(3600)
    assert item["avoided_cost_usd"] == expected, (item["avoided_cost_usd"], expected)


@then("the job avoided cost basis is the local duration fallback")
def step_avoided_cost_basis_local_fallback(context) -> None:
    assert (
        context.savings_job_item["avoided_cost_basis"] == "local_duration_fallback"
    ), context.savings_job_item["avoided_cost_basis"]


# --- Scenario: uses the Batch average once samples exist ------------------


@given("Batch samples exist for a backend with a known average billed time")
def step_batch_samples_exist(context) -> None:
    _ensure_aws_mocks(context)
    context.savings_backend = f"backend-{uuid.uuid4().hex[:8]}"
    # Two samples averaging to a known, deliberately-round figure distinct
    # from any plausible local duration_seconds, so the assertion below
    # cannot pass by coincidence if the code fell back to local duration.
    context.savings_backend_timing_table.put_item(
        Item={
            "tts_backend": context.savings_backend,
            "batch_billed_seconds_sum": Decimal(2000),
            "batch_sample_count": Decimal(2),
        }
    )
    context.savings_expected_avg_seconds = Decimal(1000)


@then("the job avoided cost is based on the Batch average")
def step_avoided_cost_based_on_batch_average(context) -> None:
    item = context.savings_job_item
    rate = Decimal(os.environ["GPU_HOURLY_RATE_USD"])
    expected = context.savings_expected_avg_seconds * rate / Decimal(3600)
    assert item["avoided_cost_usd"] == expected, (item["avoided_cost_usd"], expected)
    # Guard against a false pass: the average (1000s) must differ from this
    # job's own local duration for this assertion to be meaningful.
    assert item["duration_seconds"] != context.savings_expected_avg_seconds


@then("the job avoided cost basis is the batch average")
def step_avoided_cost_basis_batch_average(context) -> None:
    assert (
        context.savings_job_item["avoided_cost_basis"] == "batch_average"
    ), context.savings_job_item["avoided_cost_basis"]


# --- Scenario: a Batch job has no avoided cost -----------------------------


@given("a job was claimed by a Batch worker")
def step_job_claimed_by_batch_worker(context) -> None:
    _ensure_aws_mocks(context)
    _load_router(context)
    context.savings_site_id = f"site-{uuid.uuid4().hex[:8]}"
    content_hash = f"batch-job-{uuid.uuid4().hex[:8]}"
    batch_job_id = f"job-{uuid.uuid4().hex[:8]}"
    token = f"token-{content_hash}"
    now_iso = _utc_now_iso()
    context.savings_jobs_table.put_item(
        Item={
            "content_hash": content_hash,
            "status": "claimed",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Savings test text",
            "name": "Savings Test",
            "byline": "Tester",
            "site_key": "savings-site-key",
            "site_id": context.savings_site_id,
            "job_token": token,
            "claim_owner": f"batch:{batch_job_id}",
            "claimed_by": f"batch:{batch_job_id}",
            "worker_type": "batch",
            "created_at": now_iso,
            "updated_at": now_iso,
            "claimed_at": now_iso,
            "claimed_at_epoch": int(time.time()),
        }
    )
    context.savings_content_hash = content_hash
    context.savings_batch_token = token


@when("the job completes")
def step_batch_job_completes_generic(context) -> None:
    _mark_done(context, context.savings_content_hash, context.savings_batch_token)
    context.savings_job_item = context.savings_jobs_table.get_item(
        Key={"content_hash": context.savings_content_hash}
    )["Item"]


@then("the job avoided cost is zero")
def step_avoided_cost_is_zero(context) -> None:
    assert context.savings_job_item["avoided_cost_usd"] == Decimal(
        0
    ), context.savings_job_item["avoided_cost_usd"]


# --- Scenario: savings accumulate in the daily rollup ----------------------


@given("two local jobs complete for a site")
def step_two_local_jobs_complete(context) -> None:
    _ensure_aws_mocks(context)
    _load_router(context)
    context.savings_site_id = f"site-{uuid.uuid4().hex[:8]}"
    context.savings_backend = f"backend-{uuid.uuid4().hex[:8]}"
    context.savings_rollup_date = _utc_now_iso()[:10]

    total_avoided = Decimal(0)
    for _ in range(2):
        content_hash = f"local-job-{uuid.uuid4().hex[:8]}"
        token = _put_local_job(
            context,
            content_hash=content_hash,
            tts_backend=context.savings_backend,
            site_id=context.savings_site_id,
        )
        _mark_done(context, content_hash, token)
        item = context.savings_jobs_table.get_item(Key={"content_hash": content_hash})[
            "Item"
        ]
        total_avoided += item["avoided_cost_usd"]
    context.savings_expected_total_avoided = total_avoided


@then("the daily rollup avoided cost is the sum of both jobs avoided costs")
def step_rollup_avoided_cost_is_sum(context) -> None:
    item = context.savings_cost_table.get_item(
        Key={"site_id": context.savings_site_id, "date": context.savings_rollup_date}
    )["Item"]
    assert item["avoided_cost_usd"] == context.savings_expected_total_avoided, (
        item["avoided_cost_usd"],
        context.savings_expected_total_avoided,
    )


# --- Scenario: a retried backend-timing sample does not double count ------


@given("a Batch job's timing has already been sampled into the backend average")
def step_batch_timing_already_sampled(context) -> None:
    _ensure_aws_mocks(context)
    _load_batch_telemetry(context)
    context.savings_backend = f"backend-{uuid.uuid4().hex[:8]}"
    batch_job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = _utc_now_iso()
    context.savings_jobs_table.put_item(
        Item={
            "content_hash": f"batch-job-{uuid.uuid4().hex[:8]}",
            "status": "claimed",
            "claimed_by": f"batch:{batch_job_id}",
            "site_id": f"site-{uuid.uuid4().hex[:8]}",
            "tts_backend": context.savings_backend,
            "created_at": now_iso,
        }
    )
    created_at_ms = 1_700_000_000_000
    context.savings_retry_event = {
        "detail": {
            "jobId": batch_job_id,
            "status": "SUCCEEDED",
            "createdAt": created_at_ms,
            "startedAt": created_at_ms + 5_000,
            "stoppedAt": created_at_ms + 5_000 + 1_200_000,
            "container": {"instanceType": "g4dn.xlarge"},
        }
    }
    # First delivery: this is the real sample the retry must not duplicate.
    first_result = context.batch_telemetry_module.handler(
        json.loads(json.dumps(context.savings_retry_event)), None
    )
    assert first_result["status"] == "recorded", first_result

    row = context.savings_backend_timing_table.get_item(
        Key={"tts_backend": context.savings_backend}
    )["Item"]
    context.savings_sample_count_after_first = row["batch_sample_count"]
    assert context.savings_sample_count_after_first == Decimal(1)


@when("the same job's timing sample is attempted again")
def step_retry_backend_timing_sample(context) -> None:
    # A genuine EventBridge at-least-once redelivery: the same handler,
    # invoked again with an independently-deserialized copy of the exact
    # same event.
    second_result = context.batch_telemetry_module.handler(
        json.loads(json.dumps(context.savings_retry_event)), None
    )
    assert second_result["status"] == "recorded", second_result


@then("the backend average sample count is unchanged")
def step_backend_sample_count_unchanged(context) -> None:
    row = context.savings_backend_timing_table.get_item(
        Key={"tts_backend": context.savings_backend}
    )["Item"]
    assert row["batch_sample_count"] == context.savings_sample_count_after_first, (
        row["batch_sample_count"],
        context.savings_sample_count_after_first,
    )
