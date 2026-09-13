"""Behave steps for CLI Cognito login scenarios."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from auritus.auth import (
    clear_tokens,
    credentials_path,
    get_access_token,
    load_tokens,
    login_with_password,
    save_tokens,
)
from behave import given, then, when


@given("a mock Cognito USER_PASSWORD_AUTH endpoint")
def step_mock_initiate_auth(context) -> None:
    context.mock_username = "operator@example.com"
    context.mock_password = "placeholder-password"
    context.mock_auth_result = {
        "AuthenticationResult": {
            "AccessToken": "mock-access",
            "RefreshToken": "mock-refresh",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }
    }
    clear_tokens()


@when("the operator logs in with email and password")
def step_password_login(context) -> None:
    mock_client = MagicMock()
    mock_client.initiate_auth.return_value = context.mock_auth_result

    mock_config = {
        "cognito_client_id": "test-client",
        "region": "us-east-1",
    }

    with patch("auritus.auth.boto3.client", return_value=mock_client), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        login_with_password(context.mock_username, context.mock_password)


@then("Cognito tokens are cached for the CLI")
def step_tokens_cached(context) -> None:
    path = credentials_path()
    assert path.is_file()
    assert (path.stat().st_mode & 0o777) == 0o600
    cached = load_tokens()
    assert cached is not None
    assert cached.get("access_token") == "mock-access"
    assert cached.get("refresh_token") == "mock-refresh"
    assert cached.get("obtained_at") is not None


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
