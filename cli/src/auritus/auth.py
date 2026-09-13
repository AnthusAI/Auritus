"""Cognito operator authentication for the Auritus CLI."""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any

import boto3
import httpx
from botocore.exceptions import ClientError

from auritus.config import config_dir, load_config

REFRESH_SKEW_SECONDS = 10
REFRESH_TOKEN_LIFETIME_DAYS = 30
WARNING_LEAD_HOURS = 48
ALERT_MIN_INTERVAL_SECONDS = 6 * 60 * 60


class AuthError(RuntimeError):
    """Raised when Cognito login or token refresh fails."""


class RefreshExpiredError(AuthError):
    """Raised when the refresh token is dead (invalid_grant) and re-login is required."""


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
    tokens["refresh_obtained_at"] = int(time.time())
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
        error_code = ""
        try:
            error_code = str(response.json().get("error") or "")
        except (ValueError, json.JSONDecodeError):
            pass
        if error_code == "invalid_grant":
            raise RefreshExpiredError(
                "Refresh token expired or revoked. Run `auritus login` again."
            )
        raise AuthError(f"Token refresh failed: {response.status_code} {response.text}")
    refreshed = response.json()
    merged = {**tokens, **refreshed}
    merged["obtained_at"] = int(time.time())
    merged["refresh_obtained_at"] = int(time.time())
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
        except RefreshExpiredError:
            raise
        except AuthError as exc:
            raise AuthError("Session expired. Run `auritus login` again.") from exc
    return str(tokens["access_token"])


def revoke_tokens() -> None:
    """Revoke the cached refresh token at Cognito, then clear local credentials.

    Best-effort: network failures are swallowed so the local cache is still
    cleared and the operator is logged out on this machine regardless.

    :raises AuthError: If configuration is incomplete.
    """
    tokens = load_tokens()
    if tokens and tokens.get("refresh_token"):
        client_id, token_url = _token_endpoint()
        revoke_url = token_url.replace("/oauth2/token", "/oauth2/revoke")
        try:
            httpx.post(
                revoke_url,
                data={
                    "token": str(tokens["refresh_token"]),
                    "client_id": client_id,
                },
                timeout=15.0,
            )
        except httpx.HTTPError:
            pass
    clear_tokens()


def _decode_id_token_email(tokens: dict[str, Any]) -> str:
    """Return the operator email from the cached id_token, without verification.

    This is only an addressing hint for the alert endpoint; the backend
    re-verifies the user exists in Cognito before sending any email.

    :param tokens: Cached token dictionary.
    :returns: The email claim, or an empty string if unavailable.
    """
    id_token = str(tokens.get("id_token") or "")
    if not id_token or id_token.count(".") != 2:
        return ""
    try:
        payload_segment = id_token.split(".")[1]
        padded = payload_segment + "=" * (-len(payload_segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return str(payload.get("email") or "")
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return ""


def refresh_expires_at(tokens: dict[str, Any]) -> int:
    """Return the unix timestamp at which the refresh token expires.

    Computed as ``refresh_obtained_at + REFRESH_TOKEN_LIFETIME_DAYS``. With
    rotation enabled, every successful refresh resets ``refresh_obtained_at``,
    so this is "30 days since the last successful refresh".

    :param tokens: Cached token dictionary.
    :returns: Expiry unix timestamp, or 0 if unknown.
    """
    obtained = int(tokens.get("refresh_obtained_at") or 0)
    if obtained <= 0:
        return 0
    return obtained + REFRESH_TOKEN_LIFETIME_DAYS * 24 * 60 * 60


def refresh_near_expiry(tokens: dict[str, Any]) -> bool:
    """Return True if the refresh token is within the warning lead time of expiry.

    :param tokens: Cached token dictionary.
    :returns: True if a proactive re-login warning should be sent.
    """
    expires = refresh_expires_at(tokens)
    if expires <= 0:
        return False
    return time.time() >= expires - WARNING_LEAD_HOURS * 60 * 60


def _record_warning_sent(tokens: dict[str, Any]) -> None:
    """Persist a last-warning timestamp so we throttle local warnings to daily."""
    updated = {**tokens, "last_warning_sent_at": int(time.time())}
    save_tokens(updated)


def _warning_due(tokens: dict[str, Any]) -> bool:
    """Return True if a daily warning has not already been sent today."""
    last = int(tokens.get("last_warning_sent_at") or 0)
    return time.time() >= last + 24 * 60 * 60


def notify_session_state(kind: str, machine: str) -> bool:
    """Best-effort POST to the backend alert endpoint so the operator is emailed.

    The route is unauthenticated on purpose: a worker whose refresh token is
    already dead cannot present a bearer token, yet that is exactly the moment
    we need to ask for help. Network failures are swallowed and logged to stderr.

    :param kind: ``"warning"`` (near expiry) or ``"expired"`` (refresh dead).
    :param machine: Worker owner string identifying the local machine.
    :returns: True if the backend was reached (any HTTP response), False on a
        transport error so the caller can retry without throttling.
    """
    if kind not in ("warning", "expired"):
        raise ValueError(f"unknown alert kind: {kind}")
    tokens = load_tokens() or {}
    operator_email = _decode_id_token_email(tokens)
    if not operator_email:
        return True
    cfg = load_config()
    base_url = str(cfg.get("api_endpoint") or "").rstrip("/")
    if not base_url:
        return True
    try:
        response = httpx.post(
            f"{base_url}/alerts/session",
            json={
                "operator_email": operator_email,
                "kind": kind,
                "machine": machine,
            },
            timeout=10.0,
        )
    except httpx.HTTPError:
        return False
    return response.status_code < 500


def maybe_warn_near_expiry(machine: str) -> bool:
    """Send a proactive re-login warning if due and near expiry.

    :param machine: Worker owner string identifying the local machine.
    :returns: True if a warning was sent on this call.
    """
    tokens = load_tokens()
    if not tokens or not tokens.get("refresh_token"):
        return False
    if not refresh_near_expiry(tokens) or not _warning_due(tokens):
        return False
    delivered = notify_session_state("warning", machine)
    if delivered:
        _record_warning_sent(tokens)
    return delivered
