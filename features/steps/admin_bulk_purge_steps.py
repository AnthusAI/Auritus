"""Step definitions for the bulk job purge admin route."""

from __future__ import annotations

import importlib
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import boto3
from behave import given, then, when
from botocore.exceptions import ClientError
from moto import mock_aws

JOB_STATUSES = ("pending", "claimed", "done", "failed")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _operator_headers() -> dict[str, str]:
    return {"authorization": "Bearer test-operator-token-12345"}


def _ensure_handler_loaded(context) -> None:
    sys.modules.pop("handler", None)
    handler_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "cdk", "lambdas", "router"
    )
    if handler_path not in sys.path:
        sys.path.insert(0, handler_path)
    handler = importlib.import_module("handler")
    handler._sfn = Mock()
    handler._batch = Mock()
    context.handler_module = handler


def _ensure_aws_mocks(context) -> None:
    if not hasattr(context, "jobs_table") or context.jobs_table is None:
        if hasattr(context, "_mock_aws"):
            try:
                context._mock_aws.__exit__(None, None, None)
            except Exception:
                pass

        context._mock_aws = mock_aws()
        context._mock_aws.__enter__()

        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
            KeySchema=[{"AttributeName": "content_hash", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "content_hash", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "status-created_at-index",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
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
            TableName="sites",
            KeySchema=[{"AttributeName": "site_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "site_id", "AttributeType": "S"},
                {"AttributeName": "site_key", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "site_key-index",
                    "KeySchema": [{"AttributeName": "site_key", "KeyType": "HASH"}],
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
        s3.create_bucket(Bucket="audio")

        os.environ.update(
            {
                "JOBS_TABLE": "jobs",
                "SITES_TABLE": "sites",
                "AUDIO_BUCKET": "audio",
                "CLOUDFRONT_DOMAIN": "audio.example.com",
                "FALLBACK_STATE_MACHINE_ARN": "",
                "FALLBACK_SECONDS": "900",
                "DAILY_SITE_QUOTA": "100",
                "BATCH_JOB_QUEUE_NAME": "test-queue",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )

        context.jobs_table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "jobs"
        )
        context.sites_table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "sites"
        )
        context.s3_client = s3
        context.expected_total_before = 0
        context.jobs_by_status = {}


def _put_job(
    context,
    *,
    content_hash: str,
    status: str,
    site_id: str = "site-default",
    created_at: str | None = None,
    audio_key: str | None = None,
) -> None:
    created = created_at or _utc_now_iso()
    item = {
        "content_hash": content_hash,
        "status": status,
        "tts_backend": "kokoro",
        "voice_id": "af_heart",
        "text": "Bulk purge test job",
        "name": "",
        "byline": "",
        "site_key": f"key-{site_id}",
        "site_id": site_id,
        "job_token": "token",
        "created_at": created,
        "updated_at": created,
    }
    if audio_key:
        item["audio_key"] = audio_key
    context.jobs_table.put_item(Item=item)
    context.expected_total_before += 1


def _build_event(method: str, path: str, *, body: dict | None) -> dict:
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "headers": _operator_headers(),
        "body": json.dumps(body) if body is not None else None,
        "pathParameters": None,
        "queryStringParameters": None,
    }


def _call_bulk_delete(context, body: dict) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    event = _build_event("POST", "/admin/jobs/bulk-delete", body=body)
    context.response = context.handler_module.handler(event, None)
    context.response_body = json.loads(context.response["body"])


@given('twelve jobs exist for site "{site_id}"')
def step_twelve_jobs_for_site(context, site_id: str) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    context.bulk_site_id = site_id
    for index in range(12):
        status = JOB_STATUSES[index % len(JOB_STATUSES)]
        _put_job(
            context,
            content_hash=f"site-job-{index:03d}",
            status=status,
            site_id=site_id,
            created_at=_utc_now_iso(),
        )
        context.jobs_by_status.setdefault(status, []).append(f"site-job-{index:03d}")


@given('three jobs exist with status "{status}"')
def step_three_jobs_with_status(context, status: str) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    hashes = []
    for index in range(3):
        content_hash = f"status-{status}-{index}-{uuid.uuid4().hex[:8]}"
        _put_job(context, content_hash=content_hash, status=status)
        hashes.append(content_hash)
    context.jobs_by_status[status] = hashes


@given('two jobs exist with status "{status}"')
def step_two_jobs_with_status(context, status: str) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    hashes = []
    for index in range(2):
        content_hash = f"status-{status}-{index}-{uuid.uuid4().hex[:8]}"
        _put_job(context, content_hash=content_hash, status=status)
        hashes.append(content_hash)
    context.jobs_by_status[status] = hashes


@given("a job created ninety days ago")
def step_job_ninety_days_ago(context) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    content_hash = f"ninety-days-old-{uuid.uuid4().hex[:8]}"
    _put_job(
        context,
        content_hash=content_hash,
        status="done",
        created_at=_iso_days_ago(90),
    )
    context.job_ninety_days_hash = content_hash


@given("a job created today")
def step_job_created_today(context) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    content_hash = f"created-today-{uuid.uuid4().hex[:8]}"
    _put_job(
        context,
        content_hash=content_hash,
        status="done",
        created_at=_utc_now_iso(),
    )
    context.job_today_hash = content_hash


@given('three jobs exist with status "{status}" and stored audio objects')
def step_three_jobs_with_audio(context, status: str) -> None:
    _ensure_aws_mocks(context)
    _ensure_handler_loaded(context)
    hashes = []
    audio_keys = []
    for index in range(3):
        content_hash = f"audio-{status}-{index}-{uuid.uuid4().hex[:8]}"
        audio_key = f"audio/{content_hash}.wav"
        context.s3_client.put_object(Bucket="audio", Key=audio_key, Body=b"data")
        _put_job(
            context,
            content_hash=content_hash,
            status=status,
            audio_key=audio_key,
        )
        hashes.append(content_hash)
        audio_keys.append(audio_key)
    context.jobs_by_status[status] = hashes
    context.audio_keys = audio_keys


@when('the operator previews a bulk delete for site "{site_id}"')
def step_preview_bulk_delete_for_site(context, site_id: str) -> None:
    # dry_run is deliberately omitted here to prove the safety default: a
    # caller who forgets the flag must get a preview, never a real delete.
    _call_bulk_delete(context, {"site_id": site_id})


@when('the operator bulk deletes jobs with status "{status}"')
def step_bulk_delete_status(context, status: str) -> None:
    _call_bulk_delete(context, {"status": status, "dry_run": False})


@when("the operator bulk deletes jobs older than thirty days")
def step_bulk_delete_older_than_thirty(context) -> None:
    _call_bulk_delete(context, {"older_than_days": 30, "dry_run": False})


@when("the operator bulk deletes with no filter")
def step_bulk_delete_no_filter(context) -> None:
    _call_bulk_delete(context, {})


@then("the response reports twelve matching jobs")
def step_check_twelve_matched(context) -> None:
    assert context.response_body.get("matched") == 12, context.response_body


@then("no jobs are deleted")
def step_check_no_jobs_deleted(context) -> None:
    scan = context.jobs_table.scan()
    total = scan.get("Count", len(scan.get("Items") or []))
    assert (
        total == context.expected_total_before
    ), f"Expected {context.expected_total_before} jobs to remain, found {total}"


@then("the three failed jobs are removed")
def step_check_failed_removed(context) -> None:
    for content_hash in context.jobs_by_status["failed"]:
        item = context.jobs_table.get_item(Key={"content_hash": content_hash}).get(
            "Item"
        )
        assert item is None, f"Expected {content_hash} to be deleted"


@then("the two done jobs remain")
def step_check_done_remain(context) -> None:
    for content_hash in context.jobs_by_status["done"]:
        item = context.jobs_table.get_item(Key={"content_hash": content_hash}).get(
            "Item"
        )
        assert item is not None, f"Expected {content_hash} to still exist"


@then("only the ninety day old job is removed")
def step_check_only_old_removed(context) -> None:
    old_item = context.jobs_table.get_item(
        Key={"content_hash": context.job_ninety_days_hash}
    ).get("Item")
    assert old_item is None, "Expected the ninety-day-old job to be deleted"

    today_item = context.jobs_table.get_item(
        Key={"content_hash": context.job_today_hash}
    ).get("Item")
    assert today_item is not None, "Expected today's job to still exist"


@then("all three audio objects are removed from the audio bucket")
def step_check_audio_removed(context) -> None:
    for audio_key in context.audio_keys:
        try:
            context.s3_client.head_object(Bucket="audio", Key=audio_key)
            assert False, f"Audio object {audio_key} still exists in S3"
        except ClientError as exc:
            assert exc.response["Error"]["Code"] == "404", f"Unexpected error: {exc}"


@then("the response is a bad request")
def step_check_bad_request(context) -> None:
    assert (
        context.response["statusCode"] == 400
    ), f"Expected 400, got {context.response['statusCode']}"
    assert (
        context.response_body.get("error") == "filter_required"
    ), f"Expected filter_required, got {context.response_body.get('error')}"
