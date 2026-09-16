"""HTTP API router Lambda for Auritus job and site-key routes."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class ConflictError(Exception):
    """Raised when an admin action is invalid for the job's current state."""


_dynamodb = boto3.resource("dynamodb")
_s3 = boto3.client("s3")
_sfn = boto3.client("stepfunctions")

JOBS_TABLE = os.environ["JOBS_TABLE"]
SITES_TABLE = os.environ["SITES_TABLE"]
AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN", "")
FALLBACK_STATE_MACHINE_ARN = os.environ.get("FALLBACK_STATE_MACHINE_ARN", "")
FALLBACK_SECONDS = int(os.environ.get("FALLBACK_SECONDS", "900"))
DAILY_SITE_QUOTA = int(os.environ.get("DAILY_SITE_QUOTA", "100"))
BATCH_JOB_QUEUE_NAME = os.environ.get("BATCH_JOB_QUEUE_NAME", "")
USER_POOL_ID = os.environ.get("USER_POOL_ID", "")
SES_FROM_ADDRESS = os.environ.get("SES_FROM_ADDRESS", "")
ALERTS_TABLE = os.environ.get("ALERTS_TABLE", "")
GPU_HOURLY_RATE_USD = os.environ.get("GPU_HOURLY_RATE_USD", "0.526")
PLATFORM_COST_PER_JOB_USD = os.environ.get("PLATFORM_COST_PER_JOB_USD", "0.0005")
RATE_CARD_VERSION = os.environ.get("RATE_CARD_VERSION", "v1")

KOKORO_DEFAULT_VOICE_ID = "af_heart"

# The complete set of job lifecycle statuses, as also enumerated in
# _get_admin_overview's counts dict. Shared here so the unfiltered admin
# jobs listing queries the same statuses the overview reports on.
JOB_STATUSES = ("pending", "claimed", "done", "failed")

_jobs = _dynamodb.Table(JOBS_TABLE)
_sites = _dynamodb.Table(SITES_TABLE)
_alerts = _dynamodb.Table(ALERTS_TABLE) if ALERTS_TABLE else None
_cognito = boto3.client("cognito-idp")
_ses = boto3.client("ses")
_batch = boto3.client("batch")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Route API Gateway HTTP API v2 events to handlers.

    :param event: API Gateway proxy event.
    :param _context: Lambda context (unused).
    :returns: API Gateway proxy response.
    """
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    body_raw = event.get("body") or ""
    body = json.loads(body_raw) if body_raw else {}

    try:
        if method == "POST" and path == "/jobs":
            return _create_job(body, headers)
        if method == "GET" and path.startswith("/jobs/") and path != "/jobs/claimable":
            content_hash = path_params.get("hash") or path.removeprefix("/jobs/")
            return _get_job(content_hash, headers)
        if method == "POST" and path.endswith("/redeem"):
            content_hash = path_params.get("hash") or ""
            return _redeem_token(content_hash, body, headers)
        if method == "GET" and path == "/jobs/claimable":
            return _list_claimable(headers)
        if method == "PUT" and path.endswith("/claim"):
            content_hash = path_params.get("hash") or ""
            return _claim_job(content_hash, body, headers)
        if method == "PUT" and path.endswith("/done"):
            content_hash = path_params.get("hash") or ""
            return _mark_done(content_hash, body, headers)
        if method == "PUT" and path.endswith("/failed"):
            content_hash = path_params.get("hash") or ""
            return _mark_failed(content_hash, body, headers)
        if method == "POST" and path.endswith("/presign-upload"):
            content_hash = path_params.get("hash") or ""
            return _presign_upload(content_hash, headers)
        if method == "POST" and path == "/alerts/session":
            return _alert_session(body)
        if method == "POST" and path == "/sites":
            return _create_site(body, headers)
        if method == "GET" and path == "/sites":
            return _list_sites(headers)
        if method == "DELETE" and path.startswith("/sites/"):
            site_id = path_params.get("id") or path.removeprefix("/sites/")
            return _delete_site(site_id, headers)
        if method == "GET" and path == "/admin/overview":
            return _get_admin_overview(headers)
        if method == "GET" and path == "/admin/jobs":
            query_params = event.get("queryStringParameters") or {}
            return _list_admin_jobs(headers, query_params)
        if method == "GET" and path.startswith("/admin/jobs/"):
            content_hash = path_params.get("hash") or path.removeprefix("/admin/jobs/")
            return _get_admin_job(content_hash, headers)
        if method == "DELETE" and path.startswith("/admin/jobs/"):
            content_hash = path_params.get("hash") or path.removeprefix("/admin/jobs/")
            return _delete_admin_job(content_hash, headers)
        if method == "POST" and path.endswith("/regenerate"):
            content_hash = path_params.get("hash") or path.removesuffix(
                "/regenerate"
            ).removeprefix("/admin/jobs/")
            return _regenerate_admin_job(content_hash, headers)
        if method == "POST" and path.endswith("/retry"):
            content_hash = path_params.get("hash") or path.removesuffix(
                "/retry"
            ).removeprefix("/admin/jobs/")
            return _retry_admin_job(content_hash, body, headers)
        if method == "POST" and path == "/admin/queue/toggle":
            return _toggle_admin_queue(body, headers)
        if method == "POST" and path == "/admin/jobs/bulk-delete":
            return _bulk_delete_admin_jobs(body, headers)
        return _response(404, {"error": "not_found"})
    except PermissionError as exc:
        return _response(403, {"error": str(exc)})
    except ValueError as exc:
        return _response(400, {"error": str(exc)})
    except ConflictError as exc:
        return _response(409, {"error": str(exc)})
    except LookupError as exc:
        return _response(404, {"error": str(exc)})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, default=_json_default),
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"not serializable: {type(value)}")


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _resolve_voice_id(raw: str | None, tts_backend: str) -> str:
    backend = tts_backend or "kokoro"
    if backend == "kokoro":
        if not raw or raw == "default":
            return KOKORO_DEFAULT_VOICE_ID
        return raw
    if raw is None:
        return "default"
    return raw


def _content_hash(normalized_text: str, voice_id: str, tts_backend: str) -> str:
    digest = hashlib.sha256()
    digest.update(normalized_text.encode("utf-8"))
    digest.update(b"\0")
    digest.update(voice_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(tts_backend.encode("utf-8"))
    return digest.hexdigest()


def _require_operator(_headers: dict[str, str]) -> None:
    """Operator routes are protected by the API authorizer; presence is enough here."""
    auth = _headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise PermissionError("operator_auth_required")


def _check_job_token(headers: dict[str, str], content_hash: str) -> bool:
    """Return whether the request has the token belonging to a job.

    Checks both the ``X-Auritus-Job-Token`` header and the ``Authorization:
    Bearer <token>`` header for the job token.
    """
    token = headers.get("x-auritus-job-token", "")
    if not token:
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
    if not token:
        return False
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    return bool(item and item.get("job_token") == token)


def _site_from_headers(headers: dict[str, str]) -> dict[str, Any]:
    site_key = headers.get("x-auritus-site-key", "").strip()
    if not site_key:
        raise PermissionError("site_key_required")
    result = _sites.query(
        IndexName="site_key-index",
        KeyConditionExpression="site_key = :sk",
        ExpressionAttributeValues={":sk": site_key},
        Limit=1,
    )
    items = result.get("Items") or []
    if not items:
        raise PermissionError("invalid_site_key")
    site = items[0]
    if site.get("disabled"):
        raise PermissionError("site_disabled")
    return site


def _check_daily_quota(site: dict[str, Any]) -> None:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Lightweight quota via sites table attribute; production may use a dedicated counter.
    used = int(site.get("daily_usage") or 0)
    if site.get("usage_day") != day:
        used = 0
    if used >= DAILY_SITE_QUOTA:
        raise PermissionError("daily_quota_exceeded")


def _increment_quota(site_id: str) -> None:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _sites.update_item(
        Key={"site_id": site_id},
        UpdateExpression=(
            "SET usage_day = :day, "
            "daily_usage = if_not_exists(daily_usage, :zero) + :one"
        ),
        ConditionExpression="attribute_exists(site_id)",
        ExpressionAttributeValues={":day": day, ":zero": 0, ":one": 1},
    )


def _arm_fallback(content_hash: str, job_token: str, tts_backend: str) -> None:
    """Start the Step Functions fallback execution for a job, if configured.

    :param content_hash: The content hash identifying the job.
    :param job_token: The job's current single-use token.
    :param tts_backend: The TTS backend the job will use.
    """
    if not FALLBACK_STATE_MACHINE_ARN:
        return
    baseline_epoch = int(time.time())
    _sfn.start_execution(
        stateMachineArn=FALLBACK_STATE_MACHINE_ARN,
        name=f"auritus-{content_hash[:16]}-{uuid.uuid4().hex[:8]}",
        input=json.dumps(
            {
                "content_hash": content_hash,
                "job_token": job_token,
                "tts_backend": tts_backend,
                "baseline_epoch": baseline_epoch,
                "fallback_seconds": FALLBACK_SECONDS,
            }
        ),
    )


def _create_job(body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    site = _site_from_headers(headers)
    _check_daily_quota(site)

    text = body.get("text") or ""
    tts_backend = body.get("tts_backend") or "kokoro"
    voice_id = _resolve_voice_id(body.get("voice_id"), tts_backend)
    name = body.get("name") or ""
    byline = body.get("byline") or ""
    if not text.strip():
        raise ValueError("text_required")

    normalized = _normalize_text(text)
    content_hash = body.get("content_hash") or _content_hash(
        normalized, voice_id, tts_backend
    )
    now = _utc_now_iso()
    job_token = secrets.token_urlsafe(32)

    item = {
        "content_hash": content_hash,
        "status": "pending",
        "tts_backend": tts_backend,
        "voice_id": voice_id,
        "text": normalized,
        "name": name,
        "byline": byline,
        "site_key": site["site_key"],
        "site_id": site["site_id"],
        "job_token": job_token,
        "created_at": now,
        "updated_at": now,
    }

    try:
        _jobs.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(content_hash)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        existing = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
        if existing:
            return _response(
                200,
                {
                    "content_hash": content_hash,
                    "status": existing.get("status"),
                    "existing": True,
                },
            )
        raise

    _increment_quota(site["site_id"])

    _arm_fallback(content_hash, job_token, tts_backend)

    return _response(
        201,
        {"content_hash": content_hash, "status": "pending", "job_token": job_token},
    )


def _audio_url(audio_key: str | None) -> str | None:
    if not audio_key:
        return None
    return _s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": AUDIO_BUCKET, "Key": audio_key},
        ExpiresIn=3600,
    )


def _get_job(content_hash: str, headers: dict[str, str]) -> dict[str, Any]:
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item:
        raise LookupError("job_not_found")
    if not _check_job_token(headers, content_hash):
        site = _site_from_headers(headers)
        if item.get("site_id") and item["site_id"] != site["site_id"]:
            raise PermissionError("site_mismatch")

    payload = {
        "content_hash": content_hash,
        "status": item.get("status"),
        "tts_backend": item.get("tts_backend"),
        "audio_url": _audio_url(item.get("audio_key")),
        "name": item.get("name"),
        "byline": item.get("byline"),
        "worker_type": item.get("worker_type"),
        "claimed_by": item.get("claimed_by") or item.get("claim_owner"),
        "claimed_at": item.get("claimed_at"),
        "completed_at": item.get("completed_at"),
        "failed_at": item.get("failed_at"),
        "duration_seconds": item.get("duration_seconds"),
        "error_message": item.get("error_message"),
    }
    return _response(200, payload)


def _list_claimable(headers: dict[str, str]) -> dict[str, Any]:
    _require_operator(headers)
    now = int(time.time())
    result = _jobs.query(
        IndexName="status-created_at-index",
        KeyConditionExpression="#s = :pending",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":pending": "pending"},
        Limit=50,
    )
    items = list(result.get("Items") or [])
    stale = _jobs.query(
        IndexName="status-created_at-index",
        KeyConditionExpression="#s = :claimed",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":claimed": "claimed"},
        Limit=50,
    )
    for row in stale.get("Items") or []:
        deadline = int(row.get("claim_deadline") or 0)
        if deadline < now:
            items.append(row)

    return _response(
        200,
        {
            "jobs": [
                {
                    "content_hash": row["content_hash"],
                    "status": row["status"],
                    "tts_backend": row.get("tts_backend"),
                    "claim_deadline": row.get("claim_deadline"),
                    "text": row.get("text", ""),
                    "name": row.get("name", ""),
                    "byline": row.get("byline", ""),
                }
                for row in items
            ]
        },
    )


def _claim_job(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Atomically claim a job via a conditional DynamoDB UpdateItem.

    :param content_hash: The content hash identifying the job.
    :param body: Request body with ``claim_owner`` and ``claim_deadline``.
    :param headers: Request headers for auth.
    :returns: 200 on success, 409 if already claimed.
    """
    if not _check_job_token(headers, content_hash):
        _require_operator(headers)
    claim_owner = body.get("claim_owner")
    if not claim_owner:
        raise ValueError("claim_owner_required")
    deadline_val = body.get("claim_deadline")
    deadline_epoch = int(deadline_val) if deadline_val else int(time.time() + 900)
    now = _utc_now_iso()
    now_int = int(time.time())
    now_epoch = Decimal(now_int)
    worker_type = "batch" if claim_owner.startswith("batch:") else "local"
    try:
        _jobs.update_item(
            Key={"content_hash": content_hash},
            UpdateExpression=(
                "SET #status = :claimed, claim_owner = :owner, "
                "claimed_by = :owner, worker_type = :wtype, "
                "claimed_at = :now, claimed_at_epoch = :now_epoch, "
                "claim_deadline = :deadline, updated_at = :now"
            ),
            # A claimant may take a job that is pending, or reclaim one
            # whose existing claim has genuinely expired -- that's the
            # whole mutex, and it must hold the same way for every
            # claimant. This condition used to carry two more problems,
            # both found the same day live jobs were double-processed:
            #
            # 1. An extra clause, "(#status = :claimed AND :is_batch =
            #    :true_val)". :is_batch and :true_val were both literal
            #    values computed in Python before the call (worker_type ==
            #    "batch"), not DynamoDB attribute comparisons, so the
            #    clause reduced to "status = claimed AND True" for every
            #    Batch claim attempt -- Batch could steal *any*
            #    already-claimed job at any moment, deadline or not,
            #    including one a local worker was actively mid-synthesis
            #    on. Reproduced live: a local worker completed a job's
            #    mark_done, then Batch's independent, already-running
            #    fallback execution (started at job creation, per the
            #    architecture) claimed the same job anyway and overwrote it
            #    with its own (also successful) result -- both workers did
            #    the same work, and whichever finished last silently won.
            #
            # 2. The deadline check itself was "claim_deadline < :now_epoch
            #    OR claim_deadline < :now_str" -- comparing the same stored
            #    Number attribute against both a Decimal and a string
            #    literal. Only one of those can ever type-match a given
            #    item; the other is a Number-vs-String order comparison,
            #    which is invalid. claim_deadline is written as a Decimal a
            #    few lines below (and confirmed Decimal in every live
            #    record checked), so the string half was dead weight that
            #    also broke a straightforward regression test for fix #1
            #    (moto raises on the mismatched compare; real DynamoDB's
            #    behavior on it was never something to depend on either
            #    way). Compare against :now_epoch only.
            ConditionExpression=(
                "#status = :pending OR "
                "(#status = :claimed AND claim_deadline < :now_epoch)"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":claimed": "claimed",
                ":pending": "pending",
                ":owner": claim_owner,
                ":wtype": worker_type,
                ":deadline": Decimal(deadline_epoch),
                ":now": now,
                ":now_epoch": now_epoch,
            },
        )
    except ClientError as exc:
        if "ConditionalCheckFailed" in str(exc):
            return _response(409, {"error": "already_claimed"})
        raise
    return _response(
        200,
        {
            "content_hash": content_hash,
            "status": "claimed",
            "worker_type": worker_type,
            "claimed_by": claim_owner,
            "claimed_at": now,
        },
    )


def _mark_done(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    if not _check_job_token(headers, content_hash):
        _require_operator(headers)
    audio_key = body.get("audio_key")
    if not audio_key:
        raise ValueError("audio_key_required")
    now = _utc_now_iso()
    now_epoch = int(time.time())

    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    claimed_epoch = int(item.get("claimed_at_epoch", now_epoch)) if item else now_epoch
    duration_seconds = max(1, now_epoch - claimed_epoch)

    # Cost accounting, written on every completion path (local or Batch):
    #
    # - gpu_cost_usd starts at 0 here. For a local job this is correct and
    #   final -- local jobs never run on Batch, so there is no GPU cost to
    #   add. For a Batch job, this is a placeholder that batch_telemetry
    #   (triggered independently by an EventBridge "Batch Job State Change"
    #   event) will overwrite with the real figure computed from
    #   billed_seconds. In practice the Batch container calls this route
    #   itself just before it exits, and AWS only emits the state-change
    #   event once the container has actually stopped, so mark_done's write
    #   usually lands first and batch_telemetry's corrected value lands
    #   after it. That ordering is not a documented guarantee, though --
    #   Lambda cold starts or EventBridge delivery delays could plausibly
    #   let the telemetry event's Lambda invocation complete first. Either
    #   order is safe here: the two writers touch disjoint concerns
    #   (gpu_cost_usd here is a placeholder for Batch jobs; batch_telemetry
    #   recomputes it independently and does not read this value), so
    #   whichever runs second for a Batch job still leaves the record with
    #   batch_telemetry's correct figure once its event arrives -- it just
    #   means the placeholder may be briefly visible first. This is a known
    #   limitation of the current design, not a proven-safe guarantee.
    # - platform_cost_usd, cost_rate_usd_per_hour, and rate_card_version are
    #   charged/stamped on every job via the request path, since the flat
    #   platform allowance applies regardless of who processed the job and
    #   batch_telemetry never fires for local jobs.
    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=(
            "SET #status = :done, audio_key = :key, updated_at = :now, "
            "completed_at = :now, duration_seconds = :duration, "
            "gpu_cost_usd = :gpu_cost, platform_cost_usd = :platform_cost, "
            "cost_rate_usd_per_hour = :cost_rate, "
            "rate_card_version = :rate_card_version "
            "REMOVE claim_deadline"
        ),
        ConditionExpression="#status IN (:claimed, :pending)",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":done": "done",
            ":key": audio_key,
            ":now": now,
            ":duration": duration_seconds,
            ":claimed": "claimed",
            ":pending": "pending",
            ":gpu_cost": Decimal(0),
            ":platform_cost": Decimal(PLATFORM_COST_PER_JOB_USD),
            ":cost_rate": Decimal(GPU_HOURLY_RATE_USD),
            ":rate_card_version": RATE_CARD_VERSION,
        },
    )
    return _response(
        200,
        {
            "content_hash": content_hash,
            "status": "done",
            "completed_at": now,
            "duration_seconds": duration_seconds,
        },
    )


def _mark_failed(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    if not _check_job_token(headers, content_hash):
        _require_operator(headers)
    reason = body.get("reason") or "unknown_error"
    owner = body.get("owner")
    now = _utc_now_iso()
    # See the comment in _mark_done: a failed job is still costed. GPU cost
    # starts at 0 (correct and final for local jobs; a placeholder for
    # Batch jobs, overwritten by batch_telemetry's independent, correct
    # write once its EventBridge event arrives). The flat platform
    # allowance and rate-card stamp apply regardless of outcome.
    set_clauses = [
        "#status = :failed",
        "error_message = :reason",
        "failed_at = :now",
        "updated_at = :now",
        "gpu_cost_usd = :gpu_cost",
        "platform_cost_usd = :platform_cost",
        "cost_rate_usd_per_hour = :cost_rate",
        "rate_card_version = :rate_card_version",
    ]
    attr_values: dict[str, Any] = {
        ":failed": "failed",
        ":reason": reason,
        ":now": now,
        ":claimed": "claimed",
        ":pending": "pending",
        ":gpu_cost": Decimal(0),
        ":platform_cost": Decimal(PLATFORM_COST_PER_JOB_USD),
        ":cost_rate": Decimal(GPU_HOURLY_RATE_USD),
        ":rate_card_version": RATE_CARD_VERSION,
    }
    if owner:
        worker_type = "batch" if owner.startswith("batch:") else "local"
        set_clauses.extend(["claimed_by = :owner", "worker_type = :wtype"])
        attr_values[":owner"] = owner
        attr_values[":wtype"] = worker_type

    update_expr = f"SET {', '.join(set_clauses)} REMOVE claim_deadline"

    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=update_expr,
        ConditionExpression="#status IN (:claimed, :pending)",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=attr_values,
    )
    return _response(
        200,
        {
            "content_hash": content_hash,
            "status": "failed",
            "error_message": reason,
            "failed_at": now,
        },
    )


def _redeem_token(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Validate a job token and return job details plus a bearer token."""
    token = body.get("job_token") or headers.get("x-auritus-job-token", "")
    if not token:
        raise ValueError("job_token required")
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item or item.get("job_token") != token:
        raise LookupError("invalid job token")
    return _response(
        200,
        {
            "content_hash": content_hash,
            "text": item.get("text", ""),
            "voice_id": _resolve_voice_id(
                item.get("voice_id"), item.get("tts_backend", "kokoro")
            ),
            "tts_backend": item.get("tts_backend", "kokoro"),
            "name": item.get("name", ""),
            "byline": item.get("byline", ""),
            "bearer": token,
        },
    )


def _presign_upload(content_hash: str, headers: dict[str, str]) -> dict[str, Any]:
    """Generate a presigned S3 PUT URL for audio upload.

    :param content_hash: The content hash identifying the job.
    :param headers: Request headers for auth.
    :returns: 200 with ``upload_url``, ``audio_key``, and ``content_type``.
    """
    if not _check_job_token(headers, content_hash):
        _require_operator(headers)
    audio_key = f"audio/{content_hash}.wav"
    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": AUDIO_BUCKET, "Key": audio_key},
        ExpiresIn=300,
        HttpMethod="PUT",
    )
    return _response(
        200,
        {
            "upload_url": upload_url,
            "audio_key": audio_key,
            "content_type": "audio/wav",
        },
    )


def _create_site(body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    _require_operator(headers)
    label = (body.get("label") or "site").strip()
    allowed_origins = body.get("allowed_origins") or []
    site_id = str(uuid.uuid4())
    site_key = secrets.token_urlsafe(24)
    now = _utc_now_iso()
    _sites.put_item(
        Item={
            "site_id": site_id,
            "site_key": site_key,
            "label": label,
            "allowed_origins": allowed_origins,
            "disabled": False,
            "created_at": now,
            "updated_at": now,
            "daily_usage": 0,
            "usage_day": "",
        }
    )
    return _response(201, {"site_id": site_id, "site_key": site_key, "label": label})


def _list_sites(headers: dict[str, str]) -> dict[str, Any]:
    _require_operator(headers)
    scan = _sites.scan(Limit=100)
    items = scan.get("Items") or []
    return _response(
        200,
        {
            "sites": [
                {
                    "site_id": row["site_id"],
                    "label": row.get("label"),
                    "disabled": bool(row.get("disabled")),
                    "created_at": row.get("created_at"),
                }
                for row in items
            ]
        },
    )


def _delete_site(site_id: str, headers: dict[str, str]) -> dict[str, Any]:
    _require_operator(headers)
    _sites.delete_item(Key={"site_id": site_id})
    return _response(200, {"site_id": site_id, "deleted": True})


ALERT_MIN_INTERVAL_SECONDS = 6 * 60 * 60


def _alert_session(body: dict[str, Any]) -> dict[str, Any]:
    """Email the operator when a worker session is near expiry or dead.

    Unauthenticated on purpose: a worker whose refresh token is already dead
    cannot present a bearer token, yet that is exactly when it needs help.
    Abuse is bounded by verifying the email is a real Cognito user and
    rate-limiting per email/kind via a DynamoDB TTL item.

    :param body: ``{"operator_email", "kind", "machine"}``.
    :returns: 200 on send, 404 for unknown user, 429 when rate-limited.
    """
    operator_email = str(body.get("operator_email") or "").strip().lower()
    kind = str(body.get("kind") or "").strip()
    machine = str(body.get("machine") or "")
    if not operator_email or kind not in ("warning", "expired"):
        return _response(400, {"error": "invalid_request"})

    if not USER_POOL_ID:
        return _response(503, {"error": "alerts_not_configured"})
    try:
        _cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=operator_email,
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("UserNotFoundException", "ResourceNotFoundException"):
            return _response(404, {"error": "unknown_operator"})
        return _response(500, {"error": "lookup_failed"})

    rate_key = f"alert:{operator_email}:{kind}"
    now = int(time.time())
    if _alerts is None:
        return _response(503, {"error": "alerts_not_configured"})
    try:
        _alerts.put_item(
            Item={
                "alert_key": rate_key,
                "ttl": now + ALERT_MIN_INTERVAL_SECONDS,
            },
            ConditionExpression="attribute_not_exists(alert_key)",
        )
    except ClientError as exc:
        if (
            exc.response.get("Error", {}).get("Code")
            == "ConditionalCheckFailedException"
        ):
            return _response(429, {"error": "rate_limited"})
        return _response(500, {"error": "rate_limit_failed"})

    if not SES_FROM_ADDRESS or SES_FROM_ADDRESS == "auritus@example.com":
        return _response(200, {"sent": False, "reason": "ses_not_configured"})
    subject = (
        "Auritus worker session expiring soon"
        if kind == "warning"
        else "Auritus worker session expired"
    )
    action = "renew soon" if kind == "warning" else "re-authenticate now"
    body_text = (
        f"The Auritus local worker on {machine or 'an unknown machine'} reports "
        f"that its operator session is {'near expiry' if kind == 'warning' else 'expired'}. "
        f"Run `auritus login` to {action} and resume unattended operation."
    )
    try:
        _ses.send_email(
            Source=SES_FROM_ADDRESS,
            Destination={"ToAddresses": [operator_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}},
            },
        )
    except ClientError:
        return _response(200, {"sent": False, "reason": "send_failed"})
    return _response(200, {"sent": True})


def _get_admin_overview(headers: dict[str, str]) -> dict[str, Any]:
    """Return high-level KPIs: job status counts, worker race split, and queue health."""
    _require_operator(headers)
    counts = {"pending": 0, "claimed": 0, "done": 0, "failed": 0}
    worker_counts = {"local": 0, "batch": 0}
    durations: list[float] = []

    res = _jobs.scan(Limit=100)
    items = res.get("Items") or []
    for item in items:
        status = item.get("status", "unknown")
        if status in counts:
            counts[status] += 1
        wtype = item.get("worker_type")
        if wtype in worker_counts:
            worker_counts[wtype] += 1
        dur = item.get("duration_seconds")
        if dur is not None:
            durations.append(float(dur))

    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

    queue_state = "UNKNOWN"
    if BATCH_JOB_QUEUE_NAME:
        try:
            q_res = _batch.describe_job_queues(jobQueues=[BATCH_JOB_QUEUE_NAME])
            queues = q_res.get("jobQueues") or []
            if queues:
                queue_state = queues[0].get("state", "UNKNOWN")
        except (BotoCoreError, ClientError):
            queue_state = "UNKNOWN"

    return _response(
        200,
        {
            "counts": counts,
            "worker_breakdown": worker_counts,
            "avg_duration_seconds": avg_duration,
            "batch_queue_state": queue_state,
            "total_sampled_jobs": len(items),
        },
    )


def _encode_cursor(key: dict[str, Any] | None) -> str | None:
    """Encode a DynamoDB LastEvaluatedKey to a URL-safe base64 string."""
    if not key:
        return None
    raw = json.dumps(key, default=_json_default).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_cursor(token: str | None) -> dict[str, Any] | None:
    """Decode a URL-safe base64 pagination cursor to a DynamoDB key dict."""
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def _query_jobs_by_status(
    status: str, *, limit: int, start_key: dict[str, Any] | None
) -> dict[str, Any]:
    """Query one status partition of ``status-created_at-index``, newest first."""
    query_kwargs: dict[str, Any] = {
        "IndexName": "status-created_at-index",
        "KeyConditionExpression": "#s = :status",
        "ExpressionAttributeNames": {"#s": "status"},
        "ExpressionAttributeValues": {":status": status},
        "ScanIndexForward": False,
        "Limit": limit,
    }
    if start_key:
        query_kwargs["ExclusiveStartKey"] = start_key
    return _jobs.query(**query_kwargs)


def _list_admin_jobs_unfiltered(
    limit: int, cursor: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Return the ``limit`` most recent jobs across every status, newest first.

    A plain ``Scan`` with a ``Limit`` returns an arbitrary page of items in
    whatever internal partition order DynamoDB happens to read them in --
    NOT the most recently created items -- and sorting only that arbitrary
    page by ``created_at`` afterwards does not fix that: a newly created job
    can be entirely absent from the scanned page and never surface as
    "most recent" at all. This was confirmed in production: a job that
    ``GET /jobs/{hash}`` correctly reported as ``pending`` never appeared in
    this unfiltered listing, even though every job the listing did return
    was strictly older by ``created_at``.

    Instead, since ``status-created_at-index`` (partition key ``status``,
    sort key ``created_at``) is already queried correctly for the
    status-filtered case, query it once per known status with
    ``ScanIndexForward=False`` -- each such query IS genuinely sorted
    newest-first -- and merge the (at most four) results in Python.

    Pagination across a merge of independently paginated queries has no
    single natural cursor. The approach here keeps, per status, a small
    buffer of already-fetched-but-not-yet-emitted items alongside that
    status's own DynamoDB ``ExclusiveStartKey``: on every page, any status
    whose buffer is smaller than ``limit`` (the worst case, where every
    emitted item could come from one status) is topped up with one more
    query before merging, so a fetched item is only ever discarded from the
    buffer once it has actually been emitted on some page. Page one is
    always exactly correct; because nothing fetched is discarded before
    being emitted, later pages are complete and free of both gaps and
    duplicates too, modulo the ordinary snapshot-consistency caveat that
    applies to any multi-query pagination against a table that is still
    being written to between page fetches (a status's relative rank can
    shift if enough new rows land in a different status between two of the
    caller's page requests).

    The buffer is deliberately two-tier so the cursor stays small: a
    buffered-but-unemitted item is carried across pages as just its
    ``content_hash`` and ``created_at`` (the only two fields the merge/sort
    step actually needs), never its full body. Full bodies only exist
    transiently in-memory for the current request, in two ways -- freshly
    queried items arrive with a full body straight from the ``Query`` call
    (query results are never trimmed), and items surviving from a prior
    page's minimal cursor buffer get their full body fetched individually,
    but ONLY for the ones that end up on this page's emitted set. Items that
    remain buffered (fetched or carried over, but not emitted this page)
    have any full body dropped again before being written back into the
    next cursor. Without this, the cursor would embed up to
    ``limit * len(JOB_STATUSES)`` full job records -- including untruncated
    ``text`` and ``job_token`` -- base64-encoded into a ``next_token`` query
    parameter, which risks exceeding real request/URL size limits that the
    moto-based test suite has no way to catch.
    """
    per_status = cursor.get("per_status", {}) if cursor else {}

    # buffers[status] holds "buffer entries": dicts always carrying
    # content_hash and created_at (enough to sort), and carrying "item"
    # (the full DynamoDB body) only when it is already in hand for free --
    # i.e. for entries fetched fresh this request. Entries restored from
    # the cursor's minimal buffer never carry "item" yet.
    buffers: dict[str, list[dict[str, Any]]] = {}
    start_keys: dict[str, Any] = {}
    for status in JOB_STATUSES:
        state = per_status.get(status) or {}
        buffers[status] = [dict(entry) for entry in (state.get("buffer") or [])]
        start_keys[status] = state.get("start_key")

    for status in JOB_STATUSES:
        exhausted = per_status.get(status) is not None and not start_keys[status]
        if len(buffers[status]) < limit and not exhausted:
            res = _query_jobs_by_status(
                status, limit=limit, start_key=start_keys[status]
            )
            for item in res.get("Items") or []:
                buffers[status].append(
                    {
                        "content_hash": item["content_hash"],
                        "created_at": item.get("created_at", ""),
                        "item": item,
                    }
                )
            start_keys[status] = res.get("LastEvaluatedKey")

    merged: list[dict[str, Any]] = []
    for status in JOB_STATUSES:
        merged.extend(buffers[status])
    merged.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    page_entries = merged[:limit]

    # Only now -- once it's known which buffered entries actually make it
    # onto this page -- fetch full bodies for the ones that don't already
    # have one (i.e. those that came from the cursor's minimal buffer
    # rather than from a fresh query this request).
    page: list[dict[str, Any]] = []
    for entry in page_entries:
        full_item = entry.get("item")
        if full_item is None:
            full_item = _jobs.get_item(Key={"content_hash": entry["content_hash"]}).get(
                "Item"
            )
        if full_item is not None:
            page.append(full_item)

    emitted_ids = {entry["content_hash"] for entry in page_entries}
    next_per_status: dict[str, Any] = {}
    has_more = False
    for status in JOB_STATUSES:
        leftover = [
            {
                "content_hash": entry["content_hash"],
                "created_at": entry.get("created_at", ""),
            }
            for entry in buffers[status]
            if entry["content_hash"] not in emitted_ids
        ]
        next_per_status[status] = {"buffer": leftover, "start_key": start_keys[status]}
        if leftover or start_keys[status]:
            has_more = True

    next_cursor = {"multi": True, "per_status": next_per_status} if has_more else None
    return page, next_cursor


def _list_admin_jobs(
    headers: dict[str, str], query_params: dict[str, str]
) -> dict[str, Any]:
    """Return a list of generation jobs with full telemetry metadata and pagination."""
    _require_operator(headers)
    status_filter = query_params.get("status")
    limit = min(100, max(1, int(query_params.get("limit") or 25)))
    cursor = _decode_cursor(query_params.get("next_token"))

    if status_filter:
        start_key = (
            cursor if isinstance(cursor, dict) and not cursor.get("multi") else None
        )
        res = _query_jobs_by_status(status_filter, limit=limit, start_key=start_key)
        items = list(res.get("Items") or [])
        next_token = _encode_cursor(res.get("LastEvaluatedKey"))
    else:
        multi_cursor = (
            cursor if isinstance(cursor, dict) and cursor.get("multi") else None
        )
        items, next_cursor = _list_admin_jobs_unfiltered(limit, multi_cursor)
        next_token = _encode_cursor(next_cursor)

    formatted_jobs = []
    for item in items:
        audio_key = item.get("audio_key")
        formatted_jobs.append(
            {
                "content_hash": item["content_hash"],
                "status": item.get("status"),
                "tts_backend": item.get("tts_backend"),
                "voice_id": item.get("voice_id"),
                "text": str(item.get("text", ""))[:120],
                "name": item.get("name", ""),
                "byline": item.get("byline", ""),
                "site_id": item.get("site_id"),
                "worker_type": item.get("worker_type"),
                "claimed_by": item.get("claimed_by") or item.get("claim_owner"),
                "created_at": item.get("created_at"),
                "claimed_at": item.get("claimed_at"),
                "completed_at": item.get("completed_at"),
                "failed_at": item.get("failed_at"),
                "duration_seconds": item.get("duration_seconds"),
                "error_message": item.get("error_message"),
                "audio_url": _audio_url(audio_key) if audio_key else None,
            }
        )

    return _response(200, {"jobs": formatted_jobs, "next_token": next_token})


def _get_admin_job(content_hash: str, headers: dict[str, str]) -> dict[str, Any]:
    """Return full inspection details for a single job."""
    _require_operator(headers)
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item:
        raise LookupError("job_not_found")
    audio_key = item.get("audio_key")
    return _response(
        200,
        {
            "content_hash": content_hash,
            "status": item.get("status"),
            "tts_backend": item.get("tts_backend"),
            "voice_id": item.get("voice_id"),
            "text": item.get("text", ""),
            "name": item.get("name", ""),
            "byline": item.get("byline", ""),
            "site_id": item.get("site_id"),
            "site_key": item.get("site_key"),
            "worker_type": item.get("worker_type"),
            "claimed_by": item.get("claimed_by") or item.get("claim_owner"),
            "created_at": item.get("created_at"),
            "claimed_at": item.get("claimed_at"),
            "completed_at": item.get("completed_at"),
            "failed_at": item.get("failed_at"),
            "duration_seconds": item.get("duration_seconds"),
            "error_message": item.get("error_message"),
            "audio_url": _audio_url(audio_key) if audio_key else None,
            "gpu_cost_usd": item.get("gpu_cost_usd"),
            "platform_cost_usd": item.get("platform_cost_usd"),
            "cost_rate_usd_per_hour": item.get("cost_rate_usd_per_hour"),
            "rate_card_version": item.get("rate_card_version"),
        },
    )


def _delete_job_record_and_audio(item: dict[str, Any]) -> None:
    """Delete one job's S3 audio object (if any) and its DynamoDB record.

    Shared deletion core for both the single-job and bulk-delete admin
    routes. Callers are responsible for auth and for having already
    loaded ``item`` -- this does not re-fetch or re-check anything, so a
    bulk caller iterating many already-fetched items can invoke this
    directly instead of paying for a redundant per-item ``get_item`` and
    ``_require_operator`` call the way looping over ``_delete_admin_job``
    itself would.

    :param item: A full job record (must include ``content_hash``).
    """
    audio_key = item.get("audio_key")
    if audio_key:
        _s3.delete_object(Bucket=AUDIO_BUCKET, Key=audio_key)
    _jobs.delete_item(Key={"content_hash": item["content_hash"]})


def _delete_admin_job(content_hash: str, headers: dict[str, str]) -> dict[str, Any]:
    """Delete a job record and its audio artifact.

    :param content_hash: The content hash identifying the job.
    :param headers: Request headers for auth (operator-only).
    :returns: 200 with the deleted content hash.
    :raises LookupError: If no job exists for the given content hash.
    """
    _require_operator(headers)
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item:
        raise LookupError("job_not_found")
    _delete_job_record_and_audio(item)
    return _response(200, {"content_hash": content_hash, "deleted": True})


BULK_DELETE_MAX_MATCHES = 1000


def _bulk_delete_admin_jobs(
    body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Delete jobs matching a filter, dry-run by default.

    This is the most destructive route in the product, so it is built to
    fail safe in two independent ways: ``dry_run`` defaults to ``True``
    when absent from the body (the caller must explicitly pass
    ``dry_run: false`` to delete anything -- a typo'd or missing key never
    deletes), and an unfiltered call is rejected outright rather than
    treated as "match everything".

    Matching strategy and its cost, spelled out because there is
    deliberately NO index on ``site_id`` alone (see ``AuritusJobs`` in
    ``cdk/stacks/backend.py`` -- only ``status-created_at-index`` and
    ``claimed_by-index`` exist):

    * If ``status`` is given, candidates come from a single, efficient
      ``_query_jobs_by_status`` call against that status partition --
      cheap regardless of table size.
    * If ``status`` is NOT given (a bulk purge scoped only by ``site_id``
      and/or ``older_than_days``), there is no query path that can filter
      by ``site_id`` directly: doing so requires reading every job in
      every status partition and filtering client-side in Python. This
      implementation reuses ``_query_jobs_by_status`` across all
      ``JOB_STATUSES`` for that read (rather than a raw ``Scan``) so it
      goes through the same tested, correctly-paginated query path the
      rest of this file already relies on, but it is NOT cheaper than a
      full scan -- it still reads the entire table. This is acceptable
      for a bulk admin operation that is invoked rarely (retiring a
      publisher, cleaning up a bad backend), not on any hot path, but it
      is not free, and it will get slower as the table grows. A
      dedicated ``site_id`` GSI would fix this properly; it was not added
      here because doing so is a live infrastructure change requiring a
      real ``cdk deploy`` before it would work (the same caveat that
      applied to the recently-added ``claimed_by-index``), which is out
      of scope for landing this route.

    :param body: ``{"site_id": str?, "status": str?, "older_than_days":
        int?, "dry_run": bool}``. At least one of ``site_id``, ``status``,
        or ``older_than_days`` is required.
    :param headers: Request headers for auth (operator-only).
    :returns: ``{"matched": int, "deleted": int, "dry_run": bool,
        "truncated": bool}``. ``deleted`` equals ``matched`` when
        ``dry_run`` is true (nothing is actually deleted in that case);
        otherwise it is the number of jobs actually deleted. ``truncated``
        is true when more jobs may match than the ``matched`` count
        reported -- a single call caps how many candidate jobs it will
        process (``BULK_DELETE_MAX_MATCHES``) to stay well inside a
        Lambda's execution time budget; run the same filter again after a
        truncated non-dry-run delete to remove the rest.
    :raises ValueError: If no filter is supplied.
    """
    _require_operator(headers)

    site_id = body.get("site_id")
    status = body.get("status")
    older_than_days = body.get("older_than_days")
    dry_run = body.get("dry_run", True)

    if not site_id and not status and older_than_days is None:
        raise ValueError("filter_required")

    cutoff_iso = None
    if older_than_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(older_than_days))
        cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _matches(candidate: dict[str, Any]) -> bool:
        if site_id and candidate.get("site_id") != site_id:
            return False
        if (
            cutoff_iso is not None
            and str(candidate.get("created_at", "")) >= cutoff_iso
        ):
            return False
        return True

    matched: list[dict[str, Any]] = []
    truncated = False

    if status:
        start_key: dict[str, Any] | None = None
        while len(matched) < BULK_DELETE_MAX_MATCHES:
            res = _query_jobs_by_status(
                status,
                limit=min(100, BULK_DELETE_MAX_MATCHES - len(matched)),
                start_key=start_key,
            )
            for candidate_item in res.get("Items") or []:
                if _matches(candidate_item):
                    matched.append(candidate_item)
                    if len(matched) >= BULK_DELETE_MAX_MATCHES:
                        break
            start_key = res.get("LastEvaluatedKey")
            if not start_key:
                break
        if start_key:
            truncated = True
    else:
        # No status filter: every status partition must be read in full to
        # honor a site_id/age-only filter -- see the docstring above for
        # why this cannot be made cheaper without a new GSI.
        for one_status in JOB_STATUSES:
            start_key = None
            while True:
                res = _query_jobs_by_status(one_status, limit=100, start_key=start_key)
                for candidate_item in res.get("Items") or []:
                    if _matches(candidate_item):
                        if len(matched) >= BULK_DELETE_MAX_MATCHES:
                            truncated = True
                            break
                        matched.append(candidate_item)
                start_key = res.get("LastEvaluatedKey")
                if not start_key or len(matched) >= BULK_DELETE_MAX_MATCHES:
                    if start_key:
                        truncated = True
                    break
            if len(matched) >= BULK_DELETE_MAX_MATCHES:
                break

    deleted_count = 0
    if not dry_run:
        for job_item in matched:
            _delete_job_record_and_audio(job_item)
            deleted_count += 1

    return _response(
        200,
        {
            "matched": len(matched),
            "deleted": len(matched) if dry_run else deleted_count,
            "dry_run": bool(dry_run),
            "truncated": truncated,
        },
    )


def _regenerate_admin_job(content_hash: str, headers: dict[str, str]) -> dict[str, Any]:
    """Force regeneration of a job, resetting it to pending in place.

    The content hash is kept stable so an embedding page's existing
    reference keeps resolving; only the job's state is reset.

    :param content_hash: The content hash identifying the job.
    :param headers: Request headers for auth (operator-only).
    :returns: 200 with the job reset to pending.
    :raises LookupError: If no job exists for the given content hash.
    :raises ConflictError: If the job is already pending or claimed.
    """
    _require_operator(headers)
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item:
        raise LookupError("job_not_found")
    status = item.get("status")
    if status in ("pending", "claimed"):
        raise ConflictError(f"job_is_{status}")

    audio_key = item.get("audio_key")
    if audio_key:
        _s3.delete_object(Bucket=AUDIO_BUCKET, Key=audio_key)

    job_token = secrets.token_urlsafe(32)
    now = _utc_now_iso()
    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=(
            "SET #status = :pending, job_token = :token, updated_at = :now "
            "REMOVE audio_key, claimed_by, claim_owner, claimed_at, "
            "claimed_at_epoch, claim_deadline, completed_at, failed_at, "
            "duration_seconds, error_message, worker_type"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":pending": "pending",
            ":token": job_token,
            ":now": now,
        },
    )

    _arm_fallback(content_hash, job_token, item.get("tts_backend", "kokoro"))

    return _response(200, {"content_hash": content_hash, "status": "pending"})


def _retry_admin_job(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Retry a failed job, or release a stuck claim, resetting it to pending.

    A failed job is always eligible. A claimed job is eligible only if its
    stored claim deadline has passed (the worker holding it is presumed
    dead), unless the caller explicitly forces the release of a live claim.

    :param content_hash: The content hash identifying the job.
    :param body: Request body; ``force: true`` releases a live claim.
    :param headers: Request headers for auth (operator-only).
    :returns: 200 with the job reset to pending.
    :raises LookupError: If no job exists for the given content hash.
    :raises ConflictError: If the job's status makes it ineligible.
    """
    _require_operator(headers)
    item = _jobs.get_item(Key={"content_hash": content_hash}).get("Item")
    if not item:
        raise LookupError("job_not_found")

    status = item.get("status")
    force = bool(body.get("force"))

    if status == "claimed":
        deadline = item.get("claim_deadline")
        now_epoch = Decimal(int(time.time()))
        is_stale = deadline is not None and Decimal(deadline) < now_epoch
        if not is_stale and not force:
            raise ConflictError("claim_still_live")
    elif status != "failed":
        raise ConflictError(f"job_is_{status}")

    job_token = secrets.token_urlsafe(32)
    now = _utc_now_iso()
    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=(
            "SET #status = :pending, job_token = :token, updated_at = :now "
            "REMOVE claimed_by, claim_owner, claimed_at, claimed_at_epoch, "
            "claim_deadline, failed_at, error_message, worker_type"
        ),
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":pending": "pending",
            ":token": job_token,
            ":now": now,
        },
    )

    _arm_fallback(content_hash, job_token, item.get("tts_backend", "kokoro"))

    return _response(200, {"content_hash": content_hash, "status": "pending"})


def _toggle_admin_queue(
    body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    """Toggle or set the AWS Batch GPU job queue state."""
    _require_operator(headers)
    if not BATCH_JOB_QUEUE_NAME:
        raise ValueError("batch_queue_not_configured")

    desired_state = body.get("state")
    if not desired_state:
        q_res = _batch.describe_job_queues(jobQueues=[BATCH_JOB_QUEUE_NAME])
        queues = q_res.get("jobQueues") or []
        current_state = queues[0].get("state", "ENABLED") if queues else "ENABLED"
        desired_state = "DISABLED" if current_state == "ENABLED" else "ENABLED"
    else:
        desired_state = str(desired_state).upper()
        if desired_state not in ("ENABLED", "DISABLED"):
            raise ValueError("invalid_state")

    _batch.update_job_queue(
        jobQueue=BATCH_JOB_QUEUE_NAME,
        state=desired_state,
    )
    return _response(200, {"queue_name": BATCH_JOB_QUEUE_NAME, "state": desired_state})
