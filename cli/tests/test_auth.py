"""Tests for Cognito CLI authentication."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from auritus.auth import (
    AuthError,
    clear_tokens,
    get_access_token,
    load_tokens,
    login_with_password,
    save_tokens,
)


@pytest.fixture(autouse=True)
def _isolate_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr("auritus.auth.config_dir", lambda: tmp_path)
    clear_tokens()
    yield
    clear_tokens()


def test_login_with_password_caches_tokens() -> None:
    mock_client = MagicMock()
    mock_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "access-abc",
            "RefreshToken": "refresh-xyz",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }
    }
    mock_config = {"cognito_client_id": "client-id", "region": "us-east-1"}

    with (
        patch("auritus.auth.boto3.client", return_value=mock_client),
        patch("auritus.auth.load_config", return_value=mock_config),
    ):
        tokens = login_with_password("operator@example.com", "placeholder-password")

    assert tokens["access_token"] == "access-abc"
    assert tokens["refresh_token"] == "refresh-xyz"
    assert tokens.get("obtained_at") is not None
    cached = load_tokens()
    assert cached is not None
    assert cached["access_token"] == "access-abc"
    mock_client.initiate_auth.assert_called_once_with(
        ClientId="client-id",
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": "operator@example.com",
            "PASSWORD": "placeholder-password",
        },
    )


def test_login_with_password_bad_password_raises_auth_error() -> None:
    mock_client = MagicMock()
    mock_client.initiate_auth.side_effect = ClientError(
        {"Error": {"Code": "NotAuthorizedException", "Message": "Incorrect"}},
        "InitiateAuth",
    )
    mock_config = {"cognito_client_id": "client-id", "region": "us-east-1"}

    with (
        patch("auritus.auth.boto3.client", return_value=mock_client),
        patch("auritus.auth.load_config", return_value=mock_config),
        pytest.raises(AuthError, match="Invalid email or password"),
    ):
        login_with_password("operator@example.com", "wrong-placeholder")


def test_get_access_token_refreshes_when_expired() -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "refresh-xyz",
            "obtained_at": 1,
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    )
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
        "cognito_client_id": "client-id",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with (
        patch("auritus.auth.httpx.post", side_effect=fake_post),
        patch("auritus.auth.load_config", return_value=mock_config),
    ):
        token = get_access_token()

    assert token == "new-access"
    cached = load_tokens()
    assert cached is not None
    assert cached["access_token"] == "new-access"
