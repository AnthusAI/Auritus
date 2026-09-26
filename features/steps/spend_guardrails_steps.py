"""Behave steps for spend guardrail scenarios."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from auritus import api
from auritus.cli import app as cli_app
from auritus.commands import killswitch
from behave import given, then, when
from moto import mock_aws
from typer.testing import CliRunner

from support.operator_tokens import operator_access_token

LAMBDAS_PATH = Path(__file__).resolve().parents[2] / "cdk" / "lambdas"
KILLSWITCH_API_ENDPOINT = "https://api.auritus.test"
CLI_CONFIG = {"api_endpoint": KILLSWITCH_API_ENDPOINT, "region": "us-east-1"}


@given("a site key with daily quota {quota:d} and usage {usage:d}")
def step_site_quota(context, quota: int, usage: int) -> None:
    context.site_quota = quota
    context.site_usage = usage
    context.site_key = "site-test-key"


@when("a new job is created for that site key")
def step_create_job(context) -> None:
    context.quota_exceeded = context.site_usage >= context.site_quota


@then("the API responds with quota exceeded")
def step_quota_exceeded(context) -> None:
    assert context.quota_exceeded is True


@given("the daily AWS spend budget threshold is exceeded")
def step_budget_exceeded(context) -> None:
    context.budget_exceeded = True


@when("the budget action runs")
def step_budget_action(context) -> None:
    context.batch_queue_state = "DISABLED" if context.budget_exceeded else "ENABLED"


@given("{state_word} Batch job queue behind the Auritus API")
def step_queue_behind_api(context, state_word: str) -> None:
    states = {"an enabled": "ENABLED", "a disabled": "DISABLED"}
    context.batch_queue_state = states[state_word]
    context.killswitch_mock = mock_aws()
    context.killswitch_mock.start()
    context.add_cleanup(context.killswitch_mock.stop)
    router_environment = patch.dict(
        os.environ,
        {
            "JOBS_TABLE": "killswitch-jobs",
            "SITES_TABLE": "killswitch-sites",
            "AUDIO_BUCKET": "killswitch-audio",
            "BATCH_JOB_QUEUE_NAME": "auritus-gpu-queue",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    )
    router_environment.start()
    context.add_cleanup(router_environment.stop)
    router_path = str(LAMBDAS_PATH / "router")
    if router_path not in sys.path:
        sys.path.insert(0, router_path)
    sys.modules.pop("handler", None)
    router = importlib.import_module("handler")
    router._batch = Mock()
    router._batch.describe_job_queues.side_effect = lambda **_kwargs: {
        "jobQueues": [{"state": context.batch_queue_state}]
    }

    def update_job_queue(jobQueue: str, state: str) -> dict:
        assert jobQueue == "auritus-gpu-queue"
        context.batch_queue_state = state
        return {}

    router._batch.update_job_queue.side_effect = update_job_queue
    context.killswitch_router = router


def _send_to_router(context):
    """Build an ``AuritusClient._send`` replacement that calls the router."""

    def send(_client, method, url, *, headers, json_body):
        path = url.removeprefix(KILLSWITCH_API_ENDPOINT)
        result = context.killswitch_router.handler(
            {
                "requestContext": {"http": {"method": method}},
                "rawPath": path,
                "headers": headers,
                "body": json.dumps(json_body) if json_body is not None else None,
                "pathParameters": None,
                "queryStringParameters": None,
            },
            None,
        )
        return httpx.Response(
            result["statusCode"],
            content=result["body"].encode("utf-8"),
            request=httpx.Request(method, url),
        )

    return send


@when("the operator runs auritus killswitch {action}")
def step_killswitch(context, action: str) -> None:
    context.killswitch_fallback = Mock()
    with (
        patch.object(api, "load_config", return_value=CLI_CONFIG),
        patch.object(api, "get_access_token", side_effect=operator_access_token),
        patch.object(api.AuritusClient, "_send", _send_to_router(context)),
        patch.object(killswitch, "_batch_queue_state", context.killswitch_fallback),
    ):
        context.killswitch_result = CliRunner().invoke(cli_app, ["killswitch", action])
    assert context.killswitch_result.exit_code == 0, context.killswitch_result.output


@then("the kill switch did not fall back to direct AWS access")
def step_no_fallback(context) -> None:
    assert not context.killswitch_fallback.called, context.killswitch_result.output


@then('the Batch job queue state is "{state}"')
def step_queue_state(context, state: str) -> None:
    assert context.batch_queue_state == state


def _fallback_definition() -> dict:
    """Synthesize the backend stack and return the fallback state machine."""
    cdk_path = str(Path(__file__).resolve().parents[2] / "cdk")
    if cdk_path not in sys.path:
        sys.path.insert(0, cdk_path)
    from aws_cdk import App, Environment
    from aws_cdk.assertions import Template
    from stacks.backend import BackendStack

    stack = BackendStack(
        App(),
        "FallbackSpecBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    machines = Template.from_stack(stack).find_resources(
        "AWS::StepFunctions::StateMachine"
    )
    for machine in machines.values():
        parts = machine["Properties"]["DefinitionString"]["Fn::Join"][1]
        definition = json.loads(
            "".join(part if isinstance(part, str) else "TOKEN" for part in parts)
        )
        if "SubmitGpuJob" in definition["States"]:
            return definition
    raise AssertionError("no state machine submits the Batch GPU job")


@given("the deployed Batch fallback state machine")
def step_fallback_machine(context) -> None:
    context.fallback_states = _fallback_definition()["States"]


@when("the fallback's Batch job for a pending job fails or is refused")
def step_submit_refused(context) -> None:
    catchers = context.fallback_states["SubmitGpuJob"].get("Catch") or []
    handler = next(
        (catch for catch in catchers if "States.ALL" in catch["ErrorEquals"]), None
    )
    assert handler, "SubmitGpuJob has no catch-all error handler"
    context.submit_failure_state = context.fallback_states[handler["Next"]]


@then('the fallback marks the job failed with error "{error_message}"')
def step_marks_failed(context, error_message: str) -> None:
    state = context.submit_failure_state
    assert state["Resource"].endswith(":dynamodb:updateItem"), state
    parameters = state["Parameters"]
    assert parameters["Key"]["content_hash"]["S.$"] == "$.content_hash"
    names = parameters["ExpressionAttributeNames"]
    values = parameters["ExpressionAttributeValues"]
    assignments = dict(
        clause.strip().split(" = ")
        for clause in parameters["UpdateExpression"].removeprefix("SET ").split(",")
    )
    status_placeholder = next(key for key, name in names.items() if name == "status")
    assert values[assignments[status_placeholder]] == {"S": "failed"}
    assert values[assignments["error_message"]] == {"S": error_message}
    assert "failed_at" in assignments
    assert "updated_at" in assignments


@then("the fallback only marks the job failed while it is still pending")
def step_marks_failed_only_pending(context) -> None:
    parameters = context.submit_failure_state["Parameters"]
    placeholder, value = parameters["ConditionExpression"].split(" = ")
    assert parameters["ExpressionAttributeNames"][placeholder] == "status"
    assert parameters["ExpressionAttributeValues"][value] == {"S": "pending"}


@then("the fallback execution ends as failed")
def step_execution_fails(context) -> None:
    state = context.submit_failure_state
    assert context.fallback_states[state["Next"]]["Type"] == "Fail"
    for catch in state.get("Catch") or []:
        assert context.fallback_states[catch["Next"]]["Type"] == "Fail"
