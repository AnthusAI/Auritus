"""Acceptance tests for the Cognito JWKS authorizer."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

HANDLER_PATH = Path(__file__).parents[1] / "lambdas" / "authorizer" / "handler.py"
SPEC = importlib.util.spec_from_file_location("authorizer_handler", HANDLER_PATH)
authorizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authorizer)

ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_EawE35WTT"
AUDIENCE = "test-client-id"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWK = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key()))


def _jwt(**claims: str) -> str:
    """Create an RSA-signed JWT for the test Cognito issuer."""
    payload = {"iss": ISSUER, "aud": AUDIENCE, "sub": "test-user-123", **claims}
    return jwt.encode(payload, KEY, algorithm="RS256", headers={"kid": "test-key"})


def _event(token: str) -> dict[str, dict[str, str]]:
    """Create an authorizer event containing a bearer token."""
    return {"headers": {"authorization": f"Bearer {token}"}}


def _jwks_response():
    """Return a context-managed fake JWKS HTTP response."""

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps(
                {"keys": [{**JWK, "kid": "test-key", "alg": "RS256"}]}
            ).encode()

    return Response()


def setup_function():
    """Reset authorizer configuration and JWKS cache for each test."""
    authorizer.USER_POOL_ID = "us-east-1_EawE35WTT"
    authorizer.CLIENT_ID = AUDIENCE
    authorizer._jwks_cache.clear()


def test_authorizes_jwt_with_valid_signature():
    """Authorize a valid RSA-signed JWT fetched through JWKS."""
    with patch.object(
        authorizer.urllib.request, "urlopen", return_value=_jwks_response()
    ):
        result = authorizer.handler(_event(_jwt()), None)

    assert result["isAuthorized"] is True


def test_denies_request_without_authorization_header():
    """Deny a request that has no Authorization header."""
    result = authorizer.handler({"headers": {}}, None)

    assert result["isAuthorized"] is False


def test_denies_jwt_with_invalid_signature():
    """Deny a JWT whose signature does not match the JWKS key."""
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "test-user-123"},
        other_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    with patch.object(
        authorizer.urllib.request, "urlopen", return_value=_jwks_response()
    ):
        result = authorizer.handler(_event(token), None)

    assert result["isAuthorized"] is False


def test_denies_expired_jwt():
    """Deny a JWT whose expiration time has passed."""
    with patch.object(
        authorizer.urllib.request, "urlopen", return_value=_jwks_response()
    ):
        result = authorizer.handler(_event(_jwt(exp=1)), None)

    assert result["isAuthorized"] is False
