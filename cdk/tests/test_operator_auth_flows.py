"""CDK assertions for operator Cognito auth flows."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import OPERATOR_AUTH_FLOWS, BackendStack


def test_operator_clients_keep_refresh_and_password_auth() -> None:
    """CLI and console clients must keep password, SRP, and refresh auth."""
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Cognito::UserPoolClient",
        {
            "ExplicitAuthFlows": Match.array_with(
                list(OPERATOR_AUTH_FLOWS),
            )
        },
    )
    clients = template.find_resources("AWS::Cognito::UserPoolClient")
    operator_clients = [
        props["Properties"]["ExplicitAuthFlows"]
        for props in clients.values()
        if "ExplicitAuthFlows" in props["Properties"]
    ]
    assert operator_clients
    for flows in operator_clients:
        assert set(OPERATOR_AUTH_FLOWS) <= set(flows)
