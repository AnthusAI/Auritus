"""Behave hooks for Auritus feature specs."""

from __future__ import annotations

import os

from behave import use_fixture
from behave.fixture import fixture


def before_all(context) -> None:
    """Record repo root and whether integration tests are enabled."""
    context.integration = os.environ.get("AURITUS_INTEGRATION", "").lower() in (
        "1",
        "true",
        "yes",
    )
    context.aws_integration = os.environ.get("AURITUS_AWS_INTEGRATION", "").lower() in (
        "1",
        "true",
        "yes",
    )


@fixture
def reset_mocks(context):
    """Clear per-scenario mock state."""
    context.mock_jobs = {}
    context.mock_sites = {}
    yield
    context.mock_jobs = {}
    context.mock_sites = {}


def before_scenario(context, scenario) -> None:
    """Attach fixtures and honor skip tags."""
    use_fixture(reset_mocks, context)
    if "integration" in scenario.effective_tags and not context.integration:
        scenario.skip("Set AURITUS_INTEGRATION=1 to run integration scenarios")
    if "aws" in scenario.effective_tags and not context.aws_integration:
        scenario.skip("Set AURITUS_AWS_INTEGRATION=1 to run AWS scenarios")
