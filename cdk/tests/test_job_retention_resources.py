"""CDK assertions for job/audio retention (S3 lifecycle + DynamoDB TTL wiring)."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import BackendStack


def _synth_template(context: dict | None = None) -> Template:
    app = App(context=context or {})
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


def test_retention_disabled_by_default_has_no_lifecycle_rule() -> None:
    """With no retention_days context, the audio bucket has no lifecycle rule."""
    template = _synth_template()

    buckets = template.find_resources("AWS::S3::Bucket")
    assert len(buckets) == 1
    (bucket_props,) = buckets.values()
    assert "LifecycleConfiguration" not in bucket_props["Properties"]


def test_retention_disabled_by_default_sets_zero_env_var() -> None:
    """With no retention_days context, the router Lambda gets RETENTION_DAYS=0."""
    template = _synth_template()

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "handler.handler",
            "Environment": {"Variables": Match.object_like({"RETENTION_DAYS": "0"})},
        },
    )


def test_retention_enabled_sets_matching_lifecycle_and_env_var() -> None:
    """A nonzero retention_days threads the SAME value to both the S3 lifecycle
    expiration and the router Lambda's RETENTION_DAYS env var -- they must not
    be able to drift apart.
    """
    template = _synth_template({"retention_days": "90"})

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Status": "Enabled",
                                "ExpirationInDays": 90,
                            }
                        )
                    ]
                )
            }
        },
    )

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "handler.handler",
            "Environment": {"Variables": Match.object_like({"RETENTION_DAYS": "90"})},
        },
    )


def test_jobs_table_ttl_attribute_is_still_ttl() -> None:
    """The jobs table's TTL attribute is (and remains) named ``ttl``, matching
    the attribute the router Lambda's _mark_done/_mark_failed write to.
    """
    template = _synth_template({"retention_days": "90"})

    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "TimeToLiveSpecification": {
                "AttributeName": "ttl",
                "Enabled": True,
            }
        },
    )
