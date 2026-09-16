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
    """Close cost_rollups_steps.py's feature-scoped moto mock.

    That step module enters one ``mock_aws()`` and creates its tables once
    for the whole ``Daily cost rollups`` feature run (see its
    ``_ensure_aws_mocks`` docstring for why per-scenario re-entry broke
    under the full suite) rather than per-scenario like other step
    modules, stashing the open mock on ``context._rollup_mock_aws`` --
    behave step files are not loaded as ordinarily-importable modules
    under a stable ``sys.modules`` name, so ``context`` (the one object
    shared by every hook and step for the whole run) is the only reliable
    channel back to that state from here. This closes that single mock
    deterministically once the feature's last scenario finishes, so it
    cannot leak into feature files that run after it alphabetically.
    No-op for every other feature.
    """
    if feature.name != "Daily cost rollups":
        return
    from steps.cost_rollups_steps import close_rollup_mock

    close_rollup_mock(context)
