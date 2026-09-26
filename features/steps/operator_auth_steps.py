"""Step definitions for operator authentication on the Auritus API."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import Mock

import boto3
from behave import given, then, when
from moto import mock_aws

from support.operator_tokens import (
    OTHER_USER_POOL_ID,
    TEST_OPERATOR_SUB,
    install_test_user_pool,
    operator_access_token,
    shared_secret_operator_token,
    unsigned_operator_token,
)

LAMBDAS_PATH = Path(__file__).resolve().parents[2] / "cdk" / "lambdas"
PENDING_JOB_HASH = "operator-auth-pending-job"
PENDING_JOB_TOKEN = "single-use-job-token-for-operator-auth"

TOKEN_DESCRIPTIONS = {
    "an operator access token signed by the user pool": lambda: (
        operator_access_token()
    ),
    "an operator access token signed by a key the pool never published": lambda: (
        operator_access_token(signed_by_pool=False)
    ),
    "an operator access token that expired an hour ago": lambda: (
        operator_access_token(expired=True)
    ),
    "an operator ID token signed by the user pool": lambda: (
        operator_access_token(token_use="id")
    ),
    "an operator access token issued to an unknown client": lambda: (
        operator_access_token(client_id="someone-elses-client")
    ),
    "an operator access token issued by a different user pool": lambda: (
        operator_access_token(user_pool_id=OTHER_USER_POOL_ID)
    ),
    "an unsigned operator access token": unsigned_operator_token,
    "an operator access token signed with a shared secret": (
        shared_secret_operator_token
    ),
    'the bare bearer value "x"': lambda: "x",
}


def _load_authorizer():
    """Load the authorizer Lambda handler under a module name of its own."""
    install_test_user_pool()
    spec = importlib.util.spec_from_file_location(
        "operator_authorizer_handler", LAMBDAS_PATH / "authorizer" / "handler.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _start_router(context) -> None:
    """Start moto, create the router's tables, and load the router handler."""
    context.operator_auth_mock = mock_aws()
    context.operator_auth_mock.start()
    context.add_cleanup(context.operator_auth_mock.stop)
    install_test_user_pool()
    suffix = uuid.uuid4().hex[:12]
    jobs_table = f"operator-auth-jobs-{suffix}"
    sites_table = f"operator-auth-sites-{suffix}"
    audio_bucket = f"operator-auth-audio-{suffix}"
    os.environ.update(
        {
            "JOBS_TABLE": jobs_table,
            "SITES_TABLE": sites_table,
            "AUDIO_BUCKET": audio_bucket,
            "AWS_DEFAULT_REGION": "us-east-1",
        }
    )
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName=jobs_table,
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
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName=sites_table,
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
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=audio_bucket)
    router_path = str(LAMBDAS_PATH / "router")
    if router_path not in sys.path:
        sys.path.insert(0, router_path)
    sys.modules.pop("handler", None)
    context.operator_router = importlib.import_module("handler")
    context.operator_router._sfn = Mock()
    context.operator_router._batch = Mock()
    context.operator_router._batch.describe_job_queues.return_value = {
        "jobQueues": [{"state": "ENABLED"}]
    }
    context.operator_jobs_table = boto3.resource(
        "dynamodb", region_name="us-east-1"
    ).Table(jobs_table)


def _call_router(context, method: str, path: str, body: dict | None = None) -> None:
    """Invoke the router with the scenario's authorization header."""
    if not hasattr(context, "operator_router"):
        _start_router(context)
    headers = {}
    if context.operator_authorization is not None:
        headers["authorization"] = context.operator_authorization
    context.operator_response = context.operator_router.handler(
        {
            "requestContext": {"http": {"method": method}},
            "rawPath": path,
            "headers": headers,
            "body": json.dumps(body) if body is not None else None,
            "pathParameters": {"hash": PENDING_JOB_HASH},
            "queryStringParameters": None,
        },
        None,
    )


@given("a pending job awaiting a worker")
def step_pending_job(context) -> None:
    _start_router(context)
    context.operator_jobs_table.put_item(
        Item={
            "content_hash": PENDING_JOB_HASH,
            "status": "pending",
            "created_at": "2026-09-26T00:00:00Z",
            "tts_backend": "kokoro",
            "voice_id": "af_heart",
            "text": "Operator auth spec narration.",
            "job_token": PENDING_JOB_TOKEN,
        }
    )


@given("the operator presents {description}")
def step_operator_presents(context, description: str) -> None:
    if description == "no authorization header":
        context.operator_authorization = None
        return
    if description not in TOKEN_DESCRIPTIONS:
        raise NotImplementedError(f"unknown token description: {description}")
    context.operator_authorization = f"Bearer {TOKEN_DESCRIPTIONS[description]()}"


@given("the worker presents the job's own single-use job token")
def step_job_token(context) -> None:
    context.operator_authorization = f"Bearer {PENDING_JOB_TOKEN}"


@when("the authorizer checks that token")
def step_authorizer_checks(context) -> None:
    authorizer = _load_authorizer()
    headers = {}
    if context.operator_authorization is not None:
        headers["Authorization"] = context.operator_authorization
    context.authorizer_result = authorizer.handler(
        {
            "headers": headers,
            "routeArn": "arn:aws:execute-api:us-east-1:123456789012:api/$default/GET/admin/overview",
        },
        None,
    )


@when("that token calls the admin overview")
def step_call_admin_overview(context) -> None:
    _call_router(context, "GET", "/admin/overview")


@when("that token calls the job {route} route")
def step_call_job_route(context, route: str) -> None:
    requests = {
        "claim": ("PUT", {"claim_owner": "local:operator-auth-spec"}),
        "done": ("PUT", {"audio_key": f"audio/{PENDING_JOB_HASH}.mp3"}),
        "failed": ("PUT", {"error_message": "forged failure"}),
        "presign-upload": ("POST", {}),
    }
    method, body = requests[route]
    _call_router(context, method, f"/jobs/{PENDING_JOB_HASH}/{route}", body)


@then("the authorizer admits the request for that operator")
def step_authorizer_admits(context) -> None:
    assert context.authorizer_result["isAuthorized"] is True, context.authorizer_result
    assert context.authorizer_result["context"]["sub"] == TEST_OPERATOR_SUB


@then("the authorizer rejects the request")
def step_authorizer_rejects(context) -> None:
    assert context.authorizer_result["isAuthorized"] is False, context.authorizer_result


@then("the API refuses the request as forbidden")
def step_api_forbidden(context) -> None:
    assert context.operator_response["statusCode"] == 403, context.operator_response


@then("the API answers successfully")
def step_api_success(context) -> None:
    assert context.operator_response["statusCode"] == 200, context.operator_response


@then("the job is still pending and unclaimed")
def step_job_unchanged(context) -> None:
    item = context.operator_jobs_table.get_item(Key={"content_hash": PENDING_JOB_HASH})[
        "Item"
    ]
    assert item["status"] == "pending", item
    assert not item.get("claim_owner"), item
    assert not item.get("audio_key"), item
    assert not item.get("error_message"), item


@then("the job is claimed")
def step_job_claimed(context) -> None:
    item = context.operator_jobs_table.get_item(Key={"content_hash": PENDING_JOB_HASH})[
        "Item"
    ]
    assert item["status"] == "claimed", item
