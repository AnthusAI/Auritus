"""Test user pool and operator token minting for Auritus specs.

Generates one RSA signing key for a test Cognito user pool, publishes its
public half as the pool's JWKS to ``auritus_operator_auth``, and mints
access tokens signed by it (or deliberately forged, expired, or otherwise
invalid tokens) so specs exercise real signature verification.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

OPERATOR_AUTH_LAYER_PATH = (
    Path(__file__).resolve().parents[2]
    / "cdk"
    / "lambdas"
    / "operator_auth_layer"
    / "python"
)
if str(OPERATOR_AUTH_LAYER_PATH) not in sys.path:
    sys.path.insert(0, str(OPERATOR_AUTH_LAYER_PATH))

import auritus_operator_auth  # noqa: E402

TEST_USER_POOL_ID = "us-east-1_AuritusTest"
OTHER_USER_POOL_ID = "us-east-1_SomeoneElse"
TEST_CLI_CLIENT_ID = "auritus-test-cli-client"
TEST_CONSOLE_CLIENT_ID = "auritus-test-console-client"
TEST_SIGNING_KEY_ID = "auritus-test-signing-key"
TEST_OPERATOR_SUB = "operator-sub-0001"

_pool_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_forger_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StaticJwkClient(jwt.PyJWKClient):
    """A JWKS client that serves a fixed key set instead of fetching one."""

    def __init__(self, jwks: dict[str, Any]) -> None:
        super().__init__("https://jwks.invalid/.well-known/jwks.json")
        self._static_jwks = jwks

    def fetch_data(self) -> Any:
        """Return the fixed JWKS document.

        :returns: The JWKS dictionary given at construction.
        """
        return self._static_jwks


def install_test_user_pool() -> None:
    """Point the operator verifier at the test user pool and its JWKS."""
    os.environ["USER_POOL_ID"] = TEST_USER_POOL_ID
    os.environ["ALLOWED_CLIENT_IDS"] = f"{TEST_CLI_CLIENT_ID},{TEST_CONSOLE_CLIENT_ID}"
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(_pool_private_key.public_key())
    )
    public_jwk.update({"kid": TEST_SIGNING_KEY_ID, "alg": "RS256", "use": "sig"})
    issuer = auritus_operator_auth.user_pool_issuer(TEST_USER_POOL_ID)
    auritus_operator_auth._jwk_clients[issuer] = StaticJwkClient({"keys": [public_jwk]})


def operator_access_token(
    *,
    signed_by_pool: bool = True,
    expired: bool = False,
    token_use: str = "access",
    client_id: str = TEST_CLI_CLIENT_ID,
    user_pool_id: str = TEST_USER_POOL_ID,
) -> str:
    """Mint an operator token for the test user pool.

    :param signed_by_pool: Sign with the pool key; otherwise a forger's key
        presented under the pool's key id.
    :param expired: Issue the token so it expired an hour ago.
    :param token_use: The ``token_use`` claim (``access`` or ``id``).
    :param client_id: The app client the token claims to be issued to.
    :param user_pool_id: The user pool named in the issuer claim.
    :returns: A compact RS256 JWT.
    """
    install_test_user_pool()
    now = int(time.time())
    issued_at = now - 7200 if expired else now
    claims = {
        "sub": TEST_OPERATOR_SUB,
        "iss": auritus_operator_auth.user_pool_issuer(user_pool_id),
        "client_id": client_id,
        "token_use": token_use,
        "scope": "openid email profile",
        "iat": issued_at,
        "auth_time": issued_at,
        "exp": issued_at + 3600,
        "jti": f"jti-{now}",
    }
    if token_use == "id":
        claims["aud"] = client_id
    signing_key = _pool_private_key if signed_by_pool else _forger_private_key
    return jwt.encode(
        claims, signing_key, algorithm="RS256", headers={"kid": TEST_SIGNING_KEY_ID}
    )


def unsigned_operator_token() -> str:
    """Mint an ``alg: none`` token carrying otherwise valid operator claims.

    :returns: A compact JWT with an empty signature.
    """
    valid_claims = jwt.decode(
        operator_access_token(), options={"verify_signature": False}
    )
    return jwt.encode(
        valid_claims, None, algorithm="none", headers={"kid": TEST_SIGNING_KEY_ID}
    )


def shared_secret_operator_token() -> str:
    """Mint an HS256 token keyed with the pool's public JWK as the secret.

    This is the classic algorithm-confusion forgery: an attacker who knows
    the pool's public key signs with it as an HMAC secret.

    :returns: A compact HS256 JWT with otherwise valid operator claims.
    """
    valid_claims = jwt.decode(
        operator_access_token(), options={"verify_signature": False}
    )
    public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(_pool_private_key.public_key())
    signing_input = ".".join(
        _base64url(json.dumps(part, separators=(",", ":")).encode("utf-8"))
        for part in (
            {"alg": "HS256", "typ": "JWT", "kid": TEST_SIGNING_KEY_ID},
            valid_claims,
        )
    )
    signature = hmac.new(
        public_jwk.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_base64url(signature)}"


def _base64url(raw: bytes) -> str:
    """Encode bytes as unpadded base64url text.

    :param raw: The bytes to encode.
    :returns: The unpadded base64url string.
    """
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def operator_headers() -> dict[str, str]:
    """Return request headers carrying a valid operator access token.

    :returns: ``{"authorization": "Bearer <token>"}``.
    """
    return {"authorization": f"Bearer {operator_access_token()}"}
