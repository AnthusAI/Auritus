"""CDK assertions for operator Cognito auth flows."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import BackendStack


def test_operator_clients_use_password_and_srp_without_refresh_flow() -> None:
    """Refresh-token rotation forbids ALLOW_REFRESH_TOKEN_AUTH on these clients."""
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
                [
                    "ALLOW_USER_PASSWORD_AUTH",
                    "ALLOW_USER_SRP_AUTH",
                ]
            ),
            "RefreshTokenRotation": Match.object_like({"Feature": "ENABLED"}),
        },
    )
    clients = template.find_resources("AWS::Cognito::UserPoolClient")
    for props in clients.values():
        flows = set(props["Properties"].get("ExplicitAuthFlows") or [])
        if not flows:
            continue
        assert "ALLOW_USER_PASSWORD_AUTH" in flows
        assert "ALLOW_REFRESH_TOKEN_AUTH" not in flows


def test_authorizer_and_router_verify_tokens_with_the_operator_auth_layer() -> None:
    """Both token-checking functions carry the layer and the client allow-list."""
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)
    layers = template.find_resources("AWS::Lambda::LayerVersion")
    assert len(layers) == 1
    layer_id = next(iter(layers))
    functions = template.find_resources("AWS::Lambda::Function")
    for prefix in ("AuthorizerFn", "RouterFn"):
        logical_id = next(key for key in functions if key.startswith(prefix))
        props = functions[logical_id]["Properties"]
        assert {"Ref": layer_id} in props["Layers"]
        variables = props["Environment"]["Variables"]
        assert "USER_POOL_ID" in variables
        assert "ALLOWED_CLIENT_IDS" in variables
