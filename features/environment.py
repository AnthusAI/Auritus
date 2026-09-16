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


def after_feature(context, feature) -> None:
    """Close a feature-scoped moto mock, for the step modules that use one.

    ``cost_rollups_steps.py`` and ``job_cost_savings_steps.py`` each enter
    one ``mock_aws()`` and create their tables once for their whole feature
    run (see ``cost_rollups_steps._ensure_aws_mocks``'s docstring for why
    per-scenario re-entry broke under the full suite) rather than
    per-scenario like other step modules, stashing the open mock on
    ``context`` under a leading-underscore attribute -- behave step files
    are not loaded as ordinarily-importable modules under a stable
    ``sys.modules`` name, so ``context`` (the one object shared by every
    hook and step for the whole run) is the only reliable channel back to
    that state from here. This closes each single mock deterministically
    once its feature's last scenario finishes, so it cannot leak into
    feature files that run after it alphabetically. No-op for every other
    feature.
    """
    if feature.name == "Daily cost rollups":
        from steps.cost_rollups_steps import close_rollup_mock

        close_rollup_mock(context)
        return

    if feature.name == "Savings from local worker processing":
        from steps.job_cost_savings_steps import close_savings_mock

        close_savings_mock(context)
        return
