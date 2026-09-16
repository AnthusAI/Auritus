"""HTTP API router Lambda for Auritus job and site-key routes."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

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

KOKORO_DEFAULT_VOICE_ID = "af_heart"

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
        if method == "POST" and path == "/admin/queue/toggle":
            return _toggle_admin_queue(body, headers)
        return _response(404, {"error": "not_found"})
    except PermissionError as exc:
        return _response(403, {"error": str(exc)})
    except ValueError as exc:
        return _response(400, {"error": str(exc)})
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
            if existing.get("tts_backend") != tts_backend:
                print(
                    f"UPDATING {content_hash} from {existing.get('tts_backend')} to {tts_backend}",
                    flush=True,
                )
                _jobs.update_item(
                    Key={"content_hash": content_hash},
                    UpdateExpression="SET tts_backend = :backend",
                    ExpressionAttributeValues={":backend": tts_backend},
                )
                existing["tts_backend"] = tts_backend
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

    if FALLBACK_STATE_MACHINE_ARN:
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

    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=(
            "SET #status = :done, audio_key = :key, updated_at = :now, "
            "completed_at = :now, duration_seconds = :duration "
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
    set_clauses = [
        "#status = :failed",
        "error_message = :reason",
        "failed_at = :now",
        "updated_at = :now",
    ]
    attr_values: dict[str, Any] = {
        ":failed": "failed",
        ":reason": reason,
        ":now": now,
        ":claimed": "claimed",
        ":pending": "pending",
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


def _list_admin_jobs(
    headers: dict[str, str], query_params: dict[str, str]
) -> dict[str, Any]:
    """Return a list of generation jobs with full telemetry metadata and pagination."""
    _require_operator(headers)
    status_filter = query_params.get("status")
    limit = min(100, max(1, int(query_params.get("limit") or 25)))
    start_key = _decode_cursor(query_params.get("next_token"))

    query_kwargs: dict[str, Any] = {"Limit": limit}
    if start_key:
        query_kwargs["ExclusiveStartKey"] = start_key

    if status_filter:
        query_kwargs.update(
            {
                "IndexName": "status-created_at-index",
                "KeyConditionExpression": "#s = :status",
                "ExpressionAttributeNames": {"#s": "status"},
                "ExpressionAttributeValues": {":status": status_filter},
                "ScanIndexForward": False,
            }
        )
        res = _jobs.query(**query_kwargs)
    else:
        res = _jobs.scan(**query_kwargs)

    items = res.get("Items") or []
    if not status_filter:
        items.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)

    last_evaluated = res.get("LastEvaluatedKey")
    next_token = _encode_cursor(last_evaluated)

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
        },
    )


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
