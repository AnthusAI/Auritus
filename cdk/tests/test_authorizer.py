"""Acceptance tests for the Cognito JWT authorizer (shape-check version)."""

import base64
import importlib.util
import json
from pathlib import Path

HANDLER_PATH = Path(__file__).parents[1] / "lambdas" / "authorizer" / "handler.py"
SPEC = importlib.util.spec_from_file_location("authorizer_handler", HANDLER_PATH)
authorizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authorizer)


def _b64url(obj: dict) -> str:
    raw = json.dumps(obj).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _make_jwt(header: dict, payload: dict) -> str:
    h = _b64url(header)
    p = _b64url(payload)
    sig = _b64url({"sig": "fake"})
    return f"{h}.{p}.{sig}"


def test_authorizes_valid_jwt() -> None:
    """A JWT with valid structure and claims is authorized."""
    authorizer.USER_POOL_ID = "us-east-1_TestPool"
    authorizer.CLIENT_ID = "test-client-id"
    token = _make_jwt(
        {"alg": "RS256", "typ": "JWT"},
        {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
            "aud": "test-client-id",
            "sub": "user-123",
        },
    )
    event = {"headers": {"authorization": f"Bearer {token}"}}
    result = authorizer.handler(event, None)
    assert result["isAuthorized"] is True
    assert result["context"]["sub"] == "user-123"


def test_denies_missing_bearer() -> None:
    """A request without Bearer token is denied."""
    result = authorizer.handler({"headers": {}}, None)
    assert result["isAuthorized"] is False
    assert "missing_bearer" in result["context"]["reason"]


def test_denies_wrong_alg() -> None:
    """A JWT with unsupported alg is denied."""
    authorizer.USER_POOL_ID = ""
    authorizer.CLIENT_ID = ""
    token = _make_jwt(
        {"alg": "HS256", "typ": "JWT"},
        {"iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool"},
    )
    result = authorizer.handler({"headers": {"authorization": f"Bearer {token}"}}, None)
    assert result["isAuthorized"] is False
    assert "unsupported_alg" in result["context"]["reason"]


def test_denies_invalid_base64() -> None:
    """A JWT with invalid base64 is denied."""
    token = "!!!.@@@.###"
    result = authorizer.handler({"headers": {"authorization": f"Bearer {token}"}}, None)
    assert result["isAuthorized"] is False


def test_authorizes_allowed_client_ids_with_client_id_claim() -> None:
    """A JWT with client_id claim matching ALLOWED_CLIENT_IDS is authorized."""
    authorizer.USER_POOL_ID = "us-east-1_TestPool"
    authorizer.CLIENT_ID = ""
    authorizer.ALLOWED_CLIENT_IDS = ["cli-client-id", "web-console-client-id"]
    token = _make_jwt(
        {"alg": "RS256", "typ": "JWT"},
        {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
            "client_id": "web-console-client-id",
            "sub": "user-456",
        },
    )
    event = {"headers": {"authorization": f"Bearer {token}"}}
    result = authorizer.handler(event, None)
    assert result["isAuthorized"] is True
    assert result["context"]["sub"] == "user-456"


def test_denies_unauthorized_client_id() -> None:
    """A JWT with client_id not in ALLOWED_CLIENT_IDS is denied."""
    authorizer.USER_POOL_ID = "us-east-1_TestPool"
    authorizer.CLIENT_ID = ""
    authorizer.ALLOWED_CLIENT_IDS = ["cli-client-id", "web-console-client-id"]
    token = _make_jwt(
        {"alg": "RS256", "typ": "JWT"},
        {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool",
            "client_id": "unknown-client-id",
            "sub": "user-789",
        },
    )
    event = {"headers": {"authorization": f"Bearer {token}"}}
    result = authorizer.handler(event, None)
    assert result["isAuthorized"] is False
    assert "audience_mismatch" in result["context"]["reason"]
