"""Record AWS Batch billed-instance timing facts onto the job record.

The router Lambda's ``duration_seconds`` field only measures our own
container's working time (claim-to-done). It omits everything AWS actually
bills before our container claims a job: EC2 boot, ECS agent registration,
and the GPU worker image pull. Because the GPU compute environment scales
from zero (``minv_cpus=0``), every cold start pays that overhead, and on a
cold start it can exceed the actual synthesis time.

This handler listens for "Batch Job State Change" EventBridge events for
our job queue, correlates the Batch job back to its job record, and writes
timing facts (``batch_created_at``, ``batch_started_at``,
``batch_stopped_at``, ``instance_type``, ``container_seconds``,
``provisioning_seconds``, ``billed_seconds``) plus the GPU cost derived from
``billed_seconds`` (``gpu_cost_usd``, ``cost_rate_usd_per_hour``,
``rate_card_version``). It does NOT touch ``duration_seconds`` -- that field
already means something else and is read by the console -- and it does NOT
write ``platform_cost_usd``: the flat platform allowance is charged on
every job regardless of worker type, so the router Lambda's
``_mark_done``/``_mark_failed`` write it on the request path, which every
job (local or Batch) goes through, avoiding a duplicated constant.

Correlation: the Batch job's own environment overrides (which carry
``AURITUS_CONTENT_HASH``, set by the Step Functions ``BatchSubmitJob`` task)
are not reliably present on the EventBridge event -- AWS does not document
whether ``detail.container.environment`` on a Job State Change event
reflects the per-submission ``containerOverrides`` merged with the job
definition's base environment, or only the job definition's original
environment. Rather than depend on unverified behavior, this handler uses
the redundant correlation path that already exists: the Batch runner
(``worker-image/src/runner.py``) claims its job in DynamoDB as
``claimed_by = f"batch:{AWS_BATCH_JOB_ID}"``, which is unique per Batch job.
This handler queries the ``claimed_by-index`` GSI on the jobs table for
``claimed_by = f"batch:{event['detail']['jobId']}"``.

This handler also rolls up ``gpu_cost_usd`` and ``billed_seconds`` into the
``AuritusCostRollups`` table (keyed by site/date), incrementing
``batch_job_count`` once per correlated Batch job. See ``_roll_up_gpu_cost``
for the idempotency mechanism that keeps an at-least-once EventBridge
redelivery from double-counting that cost.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")

JOBS_TABLE = os.environ["JOBS_TABLE"]
CLAIMED_BY_INDEX = os.environ.get("CLAIMED_BY_INDEX", "claimed_by-index")
COST_ROLLUPS_TABLE = os.environ.get("COST_ROLLUPS_TABLE", "")
WARM_START_THRESHOLD_SECONDS = float(
    os.environ.get("WARM_START_THRESHOLD_SECONDS", "60")
)
PROVISIONING_OVERHEAD_SECONDS = float(
    os.environ.get("PROVISIONING_OVERHEAD_SECONDS", "90")
)
# GPU_HOURLY_RATE_USD and RATE_CARD_VERSION are read fresh here rather than
# depending on the router's _mark_done/_mark_failed having already stamped
# cost_rate_usd_per_hour / rate_card_version onto the job record -- a Batch
# job whose EventBridge state-change event arrives before its own mark_done
# call would otherwise see this handler skip writing them, or write stale
# defaults. Both Lambdas are configured from the same CDK context values, so
# in normal operation they agree; this handler's write is self-consistent
# either way.
GPU_HOURLY_RATE_USD = os.environ.get("GPU_HOURLY_RATE_USD", "0.526")
RATE_CARD_VERSION = os.environ.get("RATE_CARD_VERSION", "v1")

_jobs = _dynamodb.Table(JOBS_TABLE)
_cost_rollups = _dynamodb.Table(COST_ROLLUPS_TABLE) if COST_ROLLUPS_TABLE else None


def _iso(epoch_ms: int | None) -> str | None:
    """Convert a millisecond epoch timestamp to an ISO 8601 UTC string.

    :param epoch_ms: Milliseconds since the epoch, or ``None``.
    :returns: ISO 8601 string, or ``None`` if ``epoch_ms`` is ``None``.
    """
    if epoch_ms is None:
        return None
    return (
        datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def compute_timing(
    created_at_ms: int,
    started_at_ms: int | None,
    stopped_at_ms: int | None,
    *,
    warm_start_threshold_seconds: float = WARM_START_THRESHOLD_SECONDS,
    provisioning_overhead_seconds: float = PROVISIONING_OVERHEAD_SECONDS,
) -> dict[str, float]:
    """Compute container, provisioning, and total billed seconds.

    :param created_at_ms: Job creation time, milliseconds since the epoch.
    :param started_at_ms: Job start time (container running), or ``None``
        if the job never reached RUNNING (e.g. it failed before starting).
    :param stopped_at_ms: Job stop time, or ``None`` if unavailable.
    :param warm_start_threshold_seconds: If the gap between creation and
        start exceeds this, the job triggered a compute environment
        scale-up (a cold start).
    :param provisioning_overhead_seconds: Overhead seconds attributed to a
        cold start (EC2 boot, ECS agent registration, image pull).
    :returns: Dict with ``container_seconds``, ``provisioning_seconds``,
        and ``billed_seconds`` (all floats).
    """
    if started_at_ms is not None and stopped_at_ms is not None:
        container_seconds = (stopped_at_ms - started_at_ms) / 1000
    else:
        container_seconds = 0.0

    provisioning_seconds = 0.0
    if started_at_ms is not None:
        startup_gap_seconds = (started_at_ms - created_at_ms) / 1000
        if startup_gap_seconds > warm_start_threshold_seconds:
            provisioning_seconds = provisioning_overhead_seconds

    billed_seconds = container_seconds + provisioning_seconds
    return {
        "container_seconds": container_seconds,
        "provisioning_seconds": provisioning_seconds,
        "billed_seconds": billed_seconds,
    }


def _find_job_by_batch_job_id(batch_job_id: str) -> dict[str, Any] | None:
    """Look up the job record claimed by a given Batch job.

    :param batch_job_id: The AWS Batch job id (``detail.jobId``).
    :returns: The job item, or ``None`` if no job record claims it.
    """
    claimed_by = f"batch:{batch_job_id}"
    response = _jobs.query(
        IndexName=CLAIMED_BY_INDEX,
        KeyConditionExpression=Key("claimed_by").eq(claimed_by),
        Limit=1,
    )
    items = response.get("Items") or []
    return items[0] if items else None


def _roll_up_gpu_cost(
    content_hash: str,
    *,
    site_id: str | None,
    date: str,
    gpu_cost_usd: Decimal,
    billed_seconds: Decimal,
) -> None:
    """Idempotently roll up this job's GPU cost into its daily/site rollup.

    This is the highest-stakes idempotency guard in the whole cost-rollup
    feature: EventBridge delivers "at least once", so this handler can
    genuinely run more than once for the same underlying Batch job
    state-change (a redelivery, or two overlapping invocations), and GPU
    cost is real money -- not a flat, cheap-to-double-count allowance.

    The mechanism matches the router Lambda's
    ``_record_rollup_contribution`` exactly, for the same reason: claim a
    flag (``gpu_cost_rolled_up``) on the JOB record via a conditional
    ``UpdateItem`` that only succeeds once per job, and only apply the
    rollup table's ``ADD`` after winning that claim. A retried delivery
    finds the flag already set, gets ``ConditionalCheckFailedException``,
    and does nothing further -- it does NOT re-add ``gpu_cost_usd`` a
    second time. The job's own timing/cost fields (written just before
    this is called, unconditionally) are naturally idempotent on retry
    since a redelivered event carries the same ``detail`` and therefore
    recomputes the same values; only the rollup's additive ``ADD`` needed
    this extra guard.

    ``batch_job_count`` is incremented here too, exactly once per real
    Batch job that this handler successfully correlates -- see the
    docstring on the router's ``_roll_up_request_path_cost`` for why the
    router deliberately does not also increment it.

    :param content_hash: The job whose GPU cost is being recorded.
    :param site_id: The job's site, or ``None`` if unknown (skips the
        rollup entirely).
    :param date: The rollup date (``YYYY-MM-DD``), derived from the job's
        own ``created_at`` -- see the call site for why.
    :param gpu_cost_usd: The computed GPU cost for this job.
    :param billed_seconds: The computed billed seconds for this job.
    """
    if not site_id or _cost_rollups is None:
        return

    try:
        _jobs.update_item(
            Key={"content_hash": content_hash},
            UpdateExpression="SET gpu_cost_rolled_up = :true_val",
            ConditionExpression="attribute_not_exists(gpu_cost_rolled_up)",
            ExpressionAttributeValues={":true_val": True},
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            _logger.info(
                "batch_telemetry_rollup_already_recorded content_hash=%s",
                content_hash,
            )
            return
        raise

    _cost_rollups.update_item(
        Key={"site_id": site_id, "date": date},
        UpdateExpression=(
            "ADD gpu_cost_usd :gpu_cost, billed_seconds :billed_seconds, "
            "batch_job_count :one"
        ),
        ExpressionAttributeValues={
            ":gpu_cost": gpu_cost_usd,
            ":billed_seconds": billed_seconds,
            ":one": 1,
        },
    )


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Record Batch job timing facts onto the correlated job record.

    :param event: EventBridge "Batch Job State Change" event.
    :param _context: Lambda context (unused).
    :returns: Summary of what was written, or a warning if no job matched.
    """
    _logger.info("batch_telemetry_event=%s", json.dumps(event))

    detail = event.get("detail") or {}
    batch_job_id = detail.get("jobId")
    if not batch_job_id:
        _logger.warning("batch_telemetry_missing_job_id event=%s", json.dumps(event))
        return {"status": "skipped", "reason": "missing_job_id"}

    created_at_ms = detail.get("createdAt")
    started_at_ms = detail.get("startedAt")
    stopped_at_ms = detail.get("stoppedAt")
    container = detail.get("container") or {}
    instance_type = container.get("instanceType")

    job = _find_job_by_batch_job_id(batch_job_id)
    if job is None:
        _logger.warning("batch_telemetry_no_matching_job batch_job_id=%s", batch_job_id)
        return {"status": "skipped", "reason": "no_matching_job"}

    content_hash = job["content_hash"]

    timing = compute_timing(created_at_ms, started_at_ms, stopped_at_ms)

    # GPU cost in dollars: billed_seconds * hourly_rate / 3600. Decimal
    # arithmetic throughout -- this is a dollar figure written to DynamoDB,
    # and float arithmetic accumulated across many records is exactly the
    # kind of bug that's expensive to find later.
    gpu_cost_usd = (
        Decimal(str(timing["billed_seconds"]))
        * Decimal(GPU_HOURLY_RATE_USD)
        / Decimal(3600)
    )

    set_clauses = [
        "batch_created_at = :batch_created_at",
        "container_seconds = :container_seconds",
        "provisioning_seconds = :provisioning_seconds",
        "billed_seconds = :billed_seconds",
        "gpu_cost_usd = :gpu_cost_usd",
        "cost_rate_usd_per_hour = :cost_rate_usd_per_hour",
        "rate_card_version = :rate_card_version",
    ]
    expression_values: dict[str, Any] = {
        ":batch_created_at": _iso(created_at_ms),
        ":container_seconds": Decimal(str(timing["container_seconds"])),
        ":provisioning_seconds": Decimal(str(timing["provisioning_seconds"])),
        ":billed_seconds": Decimal(str(timing["billed_seconds"])),
        ":gpu_cost_usd": gpu_cost_usd,
        ":cost_rate_usd_per_hour": Decimal(GPU_HOURLY_RATE_USD),
        ":rate_card_version": RATE_CARD_VERSION,
    }

    if started_at_ms is not None:
        set_clauses.append("batch_started_at = :batch_started_at")
        expression_values[":batch_started_at"] = _iso(started_at_ms)
    if stopped_at_ms is not None:
        set_clauses.append("batch_stopped_at = :batch_stopped_at")
        expression_values[":batch_stopped_at"] = _iso(stopped_at_ms)
    if instance_type:
        set_clauses.append("instance_type = :instance_type")
        expression_values[":instance_type"] = instance_type

    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression="SET " + ", ".join(set_clauses),
        ExpressionAttributeValues=expression_values,
    )

    # Roll up the GPU cost by site/date. The date is derived from the job's
    # own created_at (when it actually ran), not from this EventBridge
    # event's own delivery time -- a job that spans midnight should be
    # attributed to the day it ran on, not the day its telemetry happened
    # to arrive. In practice these are the same day for the overwhelming
    # majority of jobs (synthesis jobs run in seconds to low minutes), so
    # this only matters for the rare job straddling UTC midnight -- but
    # getting it right costs nothing here, so there's no reason to take the
    # (event-arrival-time) shortcut.
    site_id = job.get("site_id")
    created_at = job.get("created_at")
    rollup_date = (created_at or _iso(created_at_ms) or "")[:10]
    if rollup_date:
        _roll_up_gpu_cost(
            content_hash,
            site_id=site_id,
            date=rollup_date,
            gpu_cost_usd=gpu_cost_usd,
            billed_seconds=Decimal(str(timing["billed_seconds"])),
        )
    else:
        _logger.warning(
            "batch_telemetry_rollup_skipped_no_date content_hash=%s", content_hash
        )

    _logger.info(
        "batch_telemetry_recorded content_hash=%s batch_job_id=%s billed_seconds=%s",
        content_hash,
        batch_job_id,
        timing["billed_seconds"],
    )
    return {
        "status": "recorded",
        "content_hash": content_hash,
        "batch_job_id": batch_job_id,
        **timing,
    }
