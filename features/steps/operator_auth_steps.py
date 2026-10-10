"""Step definitions for operator authentication on the Auritus API."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from behave import given, then, when

from support.router_harness import start_router
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
    """Start the scenario's router and remember its jobs table."""
    harness = start_router(context)
    context.operator_router = harness.router
    context.operator_jobs_table = harness.jobs_table


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
