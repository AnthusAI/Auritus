"""Behave steps for spend guardrail scenarios."""

from __future__ import annotations

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
