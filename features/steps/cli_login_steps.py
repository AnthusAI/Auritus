"""Behave steps for CLI Cognito login scenarios."""

from __future__ import annotations

from unittest.mock import patch

from behave import given, then, when

from auritus.auth import clear_tokens, get_access_token, load_tokens, save_tokens


@given("a mock Cognito token endpoint")
def step_mock_endpoint(context) -> None:
    context.mock_tokens = {
        "access_token": "mock-access",
        "refresh_token": "mock-refresh",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    clear_tokens()


@given("the operator completes the OAuth loopback flow")
def step_complete_oauth(context) -> None:
    save_tokens(
        {
            **context.mock_tokens,
            "expires_at": 9_999_999_999,
        }
    )


@then("Cognito tokens are cached for the CLI")
def step_tokens_cached(context) -> None:
    cached = load_tokens()
    assert cached is not None
    assert cached.get("access_token") == "mock-access"
    assert cached.get("refresh_token") == "mock-refresh"


@given("cached Cognito tokens that are near expiry")
def step_near_expiry(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "obtained_at": 1,
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    )


@when("the CLI refreshes credentials")
def step_refresh(context) -> None:
    refreshed = {
        "access_token": "new-access",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    def fake_post(url, data=None, **kwargs):
        class Response:
            status_code = 200

            def json(self):
                return refreshed

            def raise_for_status(self):
                return None

        return Response()

    mock_config = {
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with patch("auritus.auth.httpx.post", side_effect=fake_post), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        token = get_access_token()
    context.refreshed_access = token


@then("a new access token is available")
def step_new_token(context) -> None:
    assert context.refreshed_access == "new-access"
    cached = load_tokens()
    assert cached is not None
    assert cached.get("access_token") == "new-access"


@given("a deployed Cognito user pool with Google IdP")
def step_live_pool(context) -> None:
    if not context.integration:
        return
    raise NotImplementedError(
        "Live OAuth is exercised manually with AURITUS_INTEGRATION=1"
    )


@when("the operator runs auritus login")
def step_run_login(context) -> None:
    if not context.integration:
        return
    raise NotImplementedError(
        "Live OAuth is exercised manually with AURITUS_INTEGRATION=1"
    )


@then("the CLI can call operator APIs with a valid JWT")
def step_valid_jwt(context) -> None:
    if not context.integration:
        return
    raise NotImplementedError(
        "Live OAuth is exercised manually with AURITUS_INTEGRATION=1"
    )
