"""Behave steps for the GitHub release publish gate."""

from __future__ import annotations

from pathlib import Path

from behave import given, then

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


@given("the release workflow file")
def step_release_workflow(context) -> None:
    context.release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")


@then("the PyPI publish step requires AURITUS_PUBLISH_PYPI")
def step_pypi_gate(context) -> None:
    text = context.release_workflow
    assert "pypa/gh-action-pypi-publish" in text
    assert "vars.AURITUS_PUBLISH_PYPI == 'true'" in text
