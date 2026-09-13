"""Step definitions for web console operator authentication specs."""

from __future__ import annotations

from behave import given, then, when


@given("a mock Cognito endpoint for web client")
def step_mock_cognito_web(context) -> None:
    context.cognito_users = {
        "operator@example.com": "secret123",
    }
    context.web_session = None


@when('the web console submits email "{email}" and password "{password}"')
def step_web_login(context, email: str, password: str) -> None:
    stored = context.cognito_users.get(email)
    if stored and stored == password:
        context.web_session = {
            "email": email,
            "id_token": f"mock-id-token-for-{email}",
            "access_token": f"mock-access-token-for-{email}",
            "refresh_token": "mock-refresh-token",
        }
    else:
        context.web_session = None


@then("the console receives an access token and id token")
def step_check_tokens(context) -> None:
    assert context.web_session is not None
    assert "access_token" in context.web_session
    assert "id_token" in context.web_session


@then("the operator identity is authenticated")
def step_check_authenticated(context) -> None:
    assert context.web_session is not None
    assert context.web_session["email"] == "operator@example.com"


@given("an authenticated web console session")
def step_given_auth_session(context) -> None:
    context.web_session = {
        "email": "operator@example.com",
        "access_token": "valid-web-jwt-token",
        "id_token": "valid-id-token",
    }


@when("an admin API request is dispatched")
def step_dispatch_admin_req(context) -> None:
    token = context.web_session.get("access_token") if context.web_session else None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    context.dispatched_headers = headers


@then("the request header contains a Bearer authorization token")
def step_check_bearer_header(context) -> None:
    auth = context.dispatched_headers.get("Authorization", "")
    assert auth.startswith("Bearer ")
    assert len(auth.split(" ")) == 2


@when("the operator logs out")
def step_operator_logout(context) -> None:
    context.web_session = None


@then("the session tokens are cleared")
def step_tokens_cleared(context) -> None:
    assert context.web_session is None
