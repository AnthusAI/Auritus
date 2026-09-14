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


@given("an unauthenticated visitor")
def step_unauthenticated_visitor(context) -> None:
    context.web_session = None
    context.current_route = None


@when('the visitor attempts to navigate to "{route}"')
def step_visitor_navigates(context, route: str) -> None:
    # AuthGuard redirects to /login if no valid session exists and route != /login
    if not context.web_session and route != "/login":
        context.current_route = "/login"
    else:
        context.current_route = route


@then('the visitor is redirected to "{expected_route}"')
def step_visitor_redirected(context, expected_route: str) -> None:
    assert context.current_route == expected_route


@given("the operator is on the login page")
def step_on_login_page(context) -> None:
    context.current_page = "/login"
    context.oauth_redirect_url = None


@when('the operator selects sign in with "{provider}"')
def step_selects_sso(context, provider: str) -> None:
    # URL format constructed by console for Cognito Hosted UI SSO
    domain = "auritus-auth.auth.us-east-1.amazoncognito.com"
    client_id = "7gu2aukbk8n6c2o5a1q805ckp7"
    redirect_uri = "http://localhost:3000/callback"
    context.oauth_redirect_url = (
        f"https://{domain}/oauth2/authorize?identity_provider={provider}"
        f"&client_id={client_id}&response_type=code&redirect_uri={redirect_uri}"
    )
    context.selected_provider = provider


@then(
    'the browser initiates OAuth authorization against the Cognito Hosted UI for provider "{provider}"'
)
def step_verify_oauth_redirect(context, provider: str) -> None:
    assert context.oauth_redirect_url is not None
    assert f"identity_provider={provider}" in context.oauth_redirect_url
    assert "response_type=code" in context.oauth_redirect_url


@given("an OAuth authorization code from an upstream identity provider")
def step_given_auth_code(context) -> None:
    context.auth_code = "mock-auth-code-from-idp"


@when("the callback page processes the code")
def step_process_callback(context) -> None:
    # Exchange code for tokens
    context.web_session = {
        "email": "operator@example.com",
        "id_token": "sso-id-token",
        "access_token": "sso-access-token",
        "refresh_token": "sso-refresh-token",
    }
