"""CDK assertions for the Batch billing telemetry EventBridge rule and Lambda."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import BackendStack


def test_batch_telemetry_rule_and_lambda_are_wired_up() -> None:
    """The stack defines a Batch Job State Change rule targeting the telemetry Lambda."""
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "EventPattern": {
                "source": ["aws.batch"],
                "detail-type": ["Batch Job State Change"],
                "detail": Match.object_like({"status": ["SUCCEEDED", "FAILED"]}),
            },
        },
    )

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "handler.handler",
            "Environment": {
                "Variables": Match.object_like(
                    {
                        "WARM_START_THRESHOLD_SECONDS": Match.any_value(),
                        "PROVISIONING_OVERHEAD_SECONDS": Match.any_value(),
                    }
                )
            },
        },
    )


def test_jobs_table_has_claimed_by_gsi_for_batch_correlation() -> None:
    """The jobs table exposes a claimed_by GSI to correlate Batch jobs.

    This mirrors how a Batch job's own runner (worker-image/src/runner.py)
    and the router's _claim_job both write claimed_by = f"batch:{job_id}",
    which is unique per Batch job -- used because the EventBridge event's
    container environment overrides are not confirmed to carry the content
    hash reliably.
    """
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "GlobalSecondaryIndexes": Match.array_with(
                [
                    Match.object_like(
                        {
                            "IndexName": "claimed_by-index",
                            "KeySchema": [
                                {"AttributeName": "claimed_by", "KeyType": "HASH"}
                            ],
                        }
                    )
                ]
            ),
        },
    )
