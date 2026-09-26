"""Behave steps for spend guardrail scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from behave import given, then, when


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


@given("an enabled Batch job queue")
def step_queue_enabled(context) -> None:
    context.batch_queue_state = "ENABLED"


@when("the operator runs auritus killswitch disable")
def step_killswitch(context) -> None:
    context.batch_queue_state = "DISABLED"


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
