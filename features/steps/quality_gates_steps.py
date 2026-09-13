"""Behave steps for the GitHub CI quality gates."""

from __future__ import annotations

from pathlib import Path

from behave import given, then

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


@given("the CI workflow file")
def step_ci_workflow(context) -> None:
    context.ci_workflow = CI_WORKFLOW.read_text(encoding="utf-8")


@then("a step runs behave on the features directory")
def step_behave_in_ci(context) -> None:
    text = context.ci_workflow
    assert "python -m behave ../features" in text


@then("a step runs Playwright against the site")
def step_playwright_in_ci(context) -> None:
    text = context.ci_workflow
    assert "npx playwright test" in text
    assert "npx playwright install --with-deps chromium" in text
