"""Disable the Auritus Batch job queue when a budget notification fires."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

_batch = boto3.client("batch")
QUEUE_ARN = os.environ.get("BATCH_JOB_QUEUE_ARN", "")
QUEUE_NAME = os.environ.get("BATCH_JOB_QUEUE_NAME", "")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Set the configured Batch job queue state to DISABLED.

    :param event: SNS or EventBridge budget notification payload.
    :param _context: Lambda context (unused).
    :returns: Summary of the queue update.
    """
    _logger.info("budget_guard_event=%s", json.dumps(event))

    queue_name = QUEUE_NAME
    if not queue_name and QUEUE_ARN:
        queue_name = QUEUE_ARN.rsplit("/", 1)[-1]
    if not queue_name:
        raise ValueError("BATCH_JOB_QUEUE_NAME or BATCH_JOB_QUEUE_ARN is required")

    describe = _batch.describe_job_queues(jobQueues=[queue_name])
    queues = describe.get("jobQueues") or []
    if not queues:
        raise LookupError(f"job queue not found: {queue_name}")

    queue_arn = queues[0]["jobQueueArn"]
    _batch.update_job_queue(jobQueue=queue_arn, state="DISABLED")
    _logger.info("disabled_batch_queue=%s", queue_arn)
    return {"jobQueueArn": queue_arn, "state": "DISABLED"}
