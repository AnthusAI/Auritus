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
    os.environ.update(
        {
            "JOBS_TABLE": "killswitch-jobs",
            "SITES_TABLE": "killswitch-sites",
            "AUDIO_BUCKET": "killswitch-audio",
            "BATCH_JOB_QUEUE_NAME": "auritus-gpu-queue",
            "AWS_DEFAULT_REGION": "us-east-1",
        }
    )
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
