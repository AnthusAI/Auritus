"""Cognito operator authentication for the Auritus CLI."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import boto3
import httpx
from botocore.exceptions import ClientError

from auritus.config import config_dir, load_config

REFRESH_SKEW_SECONDS = 10


class AuthError(RuntimeError):
    """Raised when Cognito login or token refresh fails."""


def credentials_path() -> Path:
    """Fallback on-disk credentials path (mode 0600)."""
    return config_dir() / "credentials"


def save_tokens(tokens: dict[str, Any]) -> None:
    """Cache short-lived Cognito tokens in a mode-0600 credentials file."""
    payload = json.dumps(tokens)
    path = credentials_path()
    config_dir().mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    path.chmod(0o600)


def load_tokens() -> dict[str, Any] | None:
    """Load cached Cognito tokens from the credentials file."""
    path = credentials_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def clear_tokens() -> None:
    """Remove cached tokens."""
    path = credentials_path()
    if path.exists():
        path.unlink()


def _cognito_client_config() -> tuple[str, str]:
    cfg = load_config()
    client_id = str(cfg.get("cognito_client_id") or "")
    region = str(cfg.get("region") or "us-east-1")
    if not client_id:
        raise AuthError(
            "Missing cognito_client_id in config. "
            "Run `auritus deploy` first, or set it with `auritus config set`."
        )
    return client_id, region


def _token_endpoint() -> tuple[str, str]:
    cfg = load_config()
    client_id = str(cfg.get("cognito_client_id") or "")
    domain = str(cfg.get("cognito_domain") or "")
    region = str(cfg.get("region") or "us-east-1")
    if not client_id or not domain:
        raise AuthError(
            "Missing cognito_client_id or cognito_domain in config. "
            "Run `auritus deploy` first, or set them with `auritus config set`."
        )
    token_url = f"https://{domain}.auth.{region}.amazoncognito.com/oauth2/token"
    return client_id, token_url


def login_with_password(username: str, password: str) -> dict[str, Any]:
    """Authenticate with Cognito USER_PASSWORD_AUTH and cache tokens.

    :param username: Cognito username (typically the operator email).
    :param password: Cognito password.
    :returns: Token dictionary containing access_token, id_token, refresh_token.
    :raises AuthError: If configuration is incomplete or Cognito rejects login.
    """
    client_id, region = _cognito_client_config()
    client = boto3.client("cognito-idp", region_name=region)
    try:
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        message = exc.response.get("Error", {}).get("Message", str(exc))
        if code in ("NotAuthorizedException", "UserNotFoundException"):
            raise AuthError("Invalid email or password.") from exc
        raise AuthError(f"Cognito login failed: {message}") from exc

    challenge = response.get("ChallengeName")
    if challenge == "NEW_PASSWORD_REQUIRED":
        raise AuthError(
            "Cognito requires a new password. Set a permanent password in the "
            "Cognito user pool console, then run `auritus login` again."
        )
    if challenge:
        raise AuthError(f"Unsupported Cognito challenge: {challenge}")

    result = response.get("AuthenticationResult") or {}
    access = result.get("AccessToken")
    if not access:
        raise AuthError("Login failed: Cognito did not return an access token.")

    tokens: dict[str, Any] = {
        "access_token": access,
        "expires_in": int(result.get("ExpiresIn") or 3600),
        "token_type": result.get("TokenType") or "Bearer",
        "obtained_at": int(time.time()),
    }
    if result.get("IdToken"):
        tokens["id_token"] = result["IdToken"]
    if result.get("RefreshToken"):
        tokens["refresh_token"] = result["RefreshToken"]
    save_tokens(tokens)
    return tokens


def refresh_tokens() -> dict[str, Any]:
    """Exchange a refresh token for new access and ID tokens.

    :returns: Updated token dictionary.
    :raises AuthError: If refresh is not possible or Cognito rejects the request.
    """
    tokens = load_tokens()
    if not tokens or not tokens.get("refresh_token"):
        raise AuthError("No refresh token. Run `auritus login`.")
    client_id, token_url = _token_endpoint()
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": str(tokens["refresh_token"]),
    }
    response = httpx.post(token_url, data=data, timeout=30.0)
    if response.status_code >= 400:
        raise AuthError(f"Token refresh failed: {response.status_code} {response.text}")
    refreshed = response.json()
    merged = {**tokens, **refreshed}
    merged["obtained_at"] = int(time.time())
    if "refresh_token" not in refreshed and tokens.get("refresh_token"):
        merged["refresh_token"] = tokens["refresh_token"]
    save_tokens(merged)
    return merged


def _access_token_expired(tokens: dict[str, Any]) -> bool:
    obtained = int(tokens.get("obtained_at") or 0)
    expires_in = int(tokens.get("expires_in") or 3600)
    if obtained <= 0:
        return True
    return time.time() >= obtained + expires_in - REFRESH_SKEW_SECONDS


def get_access_token() -> str:
    """Return a valid Cognito access token, refreshing when near expiry.

    :raises AuthError: If the operator is not logged in or refresh fails.
    """
    tokens = load_tokens()
    if not tokens or "access_token" not in tokens:
        raise AuthError("Not logged in. Run `auritus login`.")
    if _access_token_expired(tokens):
        if not tokens.get("refresh_token"):
            raise AuthError("Session expired. Run `auritus login` again.")
        try:
            tokens = refresh_tokens()
        except AuthError:
            raise AuthError("Session expired. Run `auritus login` again.") from None
    return str(tokens["access_token"])
