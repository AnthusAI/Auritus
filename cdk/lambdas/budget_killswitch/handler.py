"""Disable the Auritus Batch job queue when AWS Budgets fires."""

from __future__ import annotations

import os
from typing import Any

import boto3

batch = boto3.client("batch")
BATCH_QUEUE = os.environ.get("BATCH_JOB_QUEUE_NAME", "")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """SNS / EventBridge target: disable Batch queue on budget threshold."""
    if not BATCH_QUEUE:
        return {"ok": False, "error": "BATCH_JOB_QUEUE_NAME missing"}
    batch.update_job_queue(jobQueue=BATCH_QUEUE, state="DISABLED")
    return {"ok": True, "batch_queue": BATCH_QUEUE, "state": "DISABLED", "event": event}
