"""HTTP API router Lambda for Auritus job and site-key routes."""

from __future__ import annotations

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
from botocore.exceptions import ClientError

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

_jobs = _dynamodb.Table(JOBS_TABLE)
_sites = _dynamodb.Table(SITES_TABLE)


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
        if method == "POST" and path.endswith("/presign-upload"):
            content_hash = path_params.get("hash") or ""
            return _presign_upload(content_hash, headers)
        if method == "POST" and path == "/sites":
            return _create_site(body, headers)
        if method == "GET" and path == "/sites":
            return _list_sites(headers)
        if method == "DELETE" and path.startswith("/sites/"):
            site_id = path_params.get("id") or path.removeprefix("/sites/")
            return _delete_site(site_id, headers)
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
    """Return whether the request has the token belonging to a job."""
    token = headers.get("x-auritus-job-token", "")
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
    voice_id = body.get("voice_id") or "default"
    tts_backend = body.get("tts_backend") or "higgs"
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
    claim_deadline = str(body.get("claim_deadline") or int(time.time() + 900))
    now = _utc_now_iso()
    now_epoch = str(int(time.time()))
    try:
        _jobs.update_item(
            Key={"content_hash": content_hash},
            UpdateExpression=(
                "SET #status = :claimed, claim_owner = :owner, "
                "claim_deadline = :deadline, updated_at = :now"
            ),
            ConditionExpression=(
                "#status = :pending OR "
                "(#status = :claimed AND claim_deadline < :now_epoch)"
            ),
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":claimed": "claimed",
                ":pending": "pending",
                ":owner": claim_owner,
                ":deadline": claim_deadline,
                ":now": now,
                ":now_epoch": now_epoch,
            },
        )
    except ClientError as exc:
        if "ConditionalCheckFailed" in str(exc):
            return _response(409, {"error": "already_claimed"})
        raise
    return _response(200, {"content_hash": content_hash, "status": "claimed"})


def _mark_done(
    content_hash: str, body: dict[str, Any], headers: dict[str, str]
) -> dict[str, Any]:
    if not _check_job_token(headers, content_hash):
        _require_operator(headers)
    audio_key = body.get("audio_key")
    if not audio_key:
        raise ValueError("audio_key_required")
    now = _utc_now_iso()
    _jobs.update_item(
        Key={"content_hash": content_hash},
        UpdateExpression=(
            "SET #status = :done, audio_key = :key, updated_at = :now "
            "REMOVE claim_owner, claim_deadline"
        ),
        ConditionExpression="#status IN (:claimed, :pending)",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":done": "done",
            ":key": audio_key,
            ":now": now,
            ":claimed": "claimed",
            ":pending": "pending",
        },
    )
    return _response(200, {"content_hash": content_hash, "status": "done"})


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
            "voice_id": item.get("voice_id", "default"),
            "tts_backend": item.get("tts_backend", "higgs"),
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
