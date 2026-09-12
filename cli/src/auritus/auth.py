"""Cognito Google OAuth login via local loopback listener."""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import httpx
import keyring

from auritus.config import config_dir, load_config

SERVICE_NAME = "auritus"
TOKEN_USERNAME = "cognito"
REFRESH_SKEW_SECONDS = 10


class AuthError(RuntimeError):
    """Raised when OAuth login fails."""


def credentials_path() -> Path:
    """Fallback on-disk credentials path (mode 0600)."""
    return config_dir() / "credentials"


def save_tokens(tokens: dict[str, Any]) -> None:
    """Cache short-lived Cognito tokens in keyring (or file fallback)."""
    payload = json.dumps(tokens)
    try:
        keyring.set_password(SERVICE_NAME, TOKEN_USERNAME, payload)
    except (OSError, ValueError, RuntimeError):
        path = credentials_path()
        config_dir().mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        path.chmod(0o600)


def load_tokens() -> dict[str, Any] | None:
    """Load cached Cognito tokens from the credentials file.

    The file is the source of truth — the keyring is not used
    to avoid stale-token issues on shared machines.
    """
    path = credentials_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def clear_tokens() -> None:
    """Remove cached tokens."""
    try:
        keyring.delete_password(SERVICE_NAME, TOKEN_USERNAME)
    except (OSError, ValueError, RuntimeError):
        pass
    path = credentials_path()
    if path.exists():
        path.unlink()


def _pkce_pair() -> tuple[str, str]:
    import base64

    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


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


def login_interactive(
    open_browser: bool = True, timeout_seconds: int = 300
) -> dict[str, Any]:
    """Run Cognito Google OAuth authorization-code flow on a loopback listener.

    :param open_browser: Whether to open the system browser.
    :param timeout_seconds: How long to wait for the callback.
    :returns: Token dictionary containing access_token, id_token, refresh_token.
    :raises AuthError: If configuration is incomplete or login fails.
    """
    client_id, token_url = _token_endpoint()
    cfg = load_config()
    domain = str(cfg.get("cognito_domain") or "")
    region = str(cfg.get("region") or "us-east-1")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    result: dict[str, Any] = {}
    error_box: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            params = urllib.parse.parse_qs(parsed.query)
            if params.get("state", [None])[0] != state:
                error_box.append("state mismatch")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"state mismatch")
                return
            code = params.get("code", [None])[0]
            if not code:
                error_box.append("missing code")
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"missing code")
                return
            result["code"] = code
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Auritus login complete. You can close this tab.")

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/callback"
    authorize_url = (
        f"https://{domain}.auth.{region}.amazoncognito.com/oauth2/authorize?"
        + urllib.parse.urlencode(
            {
                "client_id": client_id,
                "response_type": "code",
                "scope": "openid email profile",
                "redirect_uri": redirect_uri,
                "state": state,
                "code_challenge_method": "S256",
                "code_challenge": challenge,
                "identity_provider": "Google",
            }
        )
    )

    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    if open_browser:
        webbrowser.open(authorize_url)
    else:
        print(authorize_url)

    deadline = time.time() + timeout_seconds
    while time.time() < deadline and "code" not in result and not error_box:
        time.sleep(0.1)
    server.server_close()
    if error_box:
        raise AuthError(error_box[0])
    if "code" not in result:
        raise AuthError("Login timed out waiting for OAuth callback")

    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": result["code"],
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }
    response = httpx.post(token_url, data=data, timeout=30.0)
    if response.status_code >= 400:
        raise AuthError(
            f"Token exchange failed: {response.status_code} {response.text}"
        )
    tokens = response.json()
    tokens["obtained_at"] = int(time.time())
    save_tokens(tokens)
    return tokens


def get_access_token() -> str:
    """Return the cached Cognito access token.

    The access token is valid for 1 hour. For the local worker demo this
    is sufficient — no refresh needed. If the token expires during a long
    session, the worker will get 401 from the API and can re-authenticate.

    :raises AuthError: If the operator is not logged in.
    """
    tokens = load_tokens()
    if not tokens or "access_token" not in tokens:
        raise AuthError("Not logged in. Run `auritus login`.")
    return str(tokens["access_token"])
