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
``provisioning_seconds``, ``billed_seconds``). It does NOT touch
``duration_seconds`` -- that field already means something else and is read
by the console -- and it does NOT calculate a dollar cost; that's a
separate, blocked-on-this story.

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

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")

JOBS_TABLE = os.environ["JOBS_TABLE"]
CLAIMED_BY_INDEX = os.environ.get("CLAIMED_BY_INDEX", "claimed_by-index")
WARM_START_THRESHOLD_SECONDS = float(
    os.environ.get("WARM_START_THRESHOLD_SECONDS", "60")
)
PROVISIONING_OVERHEAD_SECONDS = float(
    os.environ.get("PROVISIONING_OVERHEAD_SECONDS", "90")
)

_jobs = _dynamodb.Table(JOBS_TABLE)


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

    set_clauses = [
        "batch_created_at = :batch_created_at",
        "container_seconds = :container_seconds",
        "provisioning_seconds = :provisioning_seconds",
        "billed_seconds = :billed_seconds",
    ]
    expression_values: dict[str, Any] = {
        ":batch_created_at": _iso(created_at_ms),
        ":container_seconds": Decimal(str(timing["container_seconds"])),
        ":provisioning_seconds": Decimal(str(timing["provisioning_seconds"])),
        ":billed_seconds": Decimal(str(timing["billed_seconds"])),
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
