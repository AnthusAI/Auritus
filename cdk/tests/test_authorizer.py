"""Acceptance tests for the Cognito JWT shape-check authorizer."""

import base64
import importlib.util
import json
from pathlib import Path

HANDLER_PATH = Path(__file__).parents[1] / "lambdas" / "authorizer" / "handler.py"
SPEC = importlib.util.spec_from_file_location("authorizer_handler", HANDLER_PATH)
authorizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authorizer)


ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EawE35WTT"
AUDIENCE = "test-client-id"


def _encode_segment(value: dict[str, str]) -> str:
    """Encode a JWT header or payload as an unpadded base64url segment."""
    encoded = base64.urlsafe_b64encode(json.dumps(value).encode("utf-8"))
    return encoded.rstrip(b"=").decode("ascii")


def _jwt(
    header: dict[str, str] | None = None, payload: dict[str, str] | None = None
) -> str:
    """Construct a fake JWT with an arbitrary base64url signature."""
    header = header or {"alg": "RS256", "typ": "JWT"}
    payload = payload or {"iss": ISSUER, "aud": AUDIENCE, "sub": "test-user-123"}
    return f"{_encode_segment(header)}.{_encode_segment(payload)}.c2lnbmF0dXJl"


def test_authorizes_jwt_with_valid_structure_and_claims():
    """Authorize a three-part JWT with valid algorithm and claims."""
    authorizer.USER_POOL_ID = "us-east-1_EawE35WTT"
    authorizer.CLIENT_ID = AUDIENCE

    result = authorizer.handler(
        {"headers": {"authorization": f"Bearer {_jwt()}"}}, None
    )

    assert result["isAuthorized"] is True


def test_denies_request_without_authorization_header():
    """Deny a request that has no Authorization header."""
    result = authorizer.handler({"headers": {}}, None)

    assert result["isAuthorized"] is False


def test_denies_jwt_with_wrong_algorithm():
    """Deny a JWT that does not use an allowed RSA algorithm."""
    authorizer.USER_POOL_ID = "us-east-1_EawE35WTT"
    authorizer.CLIENT_ID = AUDIENCE

    result = authorizer.handler(
        {
            "headers": {
                "authorization": f"Bearer {_jwt({'alg': 'HS256', 'typ': 'JWT'})}"
            }
        },
        None,
    )

    assert result["isAuthorized"] is False


def test_denies_jwt_with_invalid_base64():
    """Deny a JWT containing an invalid base64 header segment."""
    authorizer.USER_POOL_ID = "us-east-1_EawE35WTT"
    authorizer.CLIENT_ID = AUDIENCE

    result = authorizer.handler(
        {"headers": {"authorization": "Bearer !!!.invalid.c2lnbmF0dXJl"}}, None
    )

    assert result["isAuthorized"] is False
