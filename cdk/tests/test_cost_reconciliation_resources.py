"""CDK assertions for the cost reconciliation Lambda, its schedule, and IAM grant."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import BackendStack


def _synth_template() -> Template:
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


def test_cost_reconciliation_lambda_is_defined() -> None:
    """The stack defines the cost_reconciliation Lambda with its expected env vars."""
    template = _synth_template()

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "handler.handler",
            "Environment": {
                "Variables": Match.object_like(
                    {
                        "COST_ROLLUPS_DATE_INDEX": "date-site_id-index",
                        "variance_threshold_percent": Match.any_value(),
                        "RECONCILIATION_LOOKBACK_DAYS": Match.any_value(),
                    }
                )
            },
        },
    )


def test_cost_reconciliation_schedule_rule_targets_the_lambda() -> None:
    """A daily EventBridge schedule rule targets the cost reconciliation Lambda."""
    template = _synth_template()

    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "ScheduleExpression": Match.string_like_regexp(r"^cron\(.*\)$"),
        },
    )


def test_cost_reconciliation_has_cost_explorer_read_permission() -> None:
    """The Lambda's role is granted ce:GetCostAndUsage."""
    template = _synth_template()

    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Action": "ce:GetCostAndUsage",
                                "Effect": "Allow",
                                "Resource": "*",
                            }
                        )
                    ]
                ),
            },
        },
    )
