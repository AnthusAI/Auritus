"""Cognito operator access-token verification shared by Auritus Lambdas.

The API Gateway authorizer and the router both call
:func:`verify_operator_token`. A token passes only when its RS256 signature
verifies against the user pool's published JWKS, its issuer is exactly the
configured user pool, it has not expired, it is an access token, and it was
issued to one of the allowed Auritus app clients. Missing configuration
denies every token.
"""

from __future__ import annotations

import os
from typing import Any

import jwt

REQUIRED_CLAIMS = ["exp", "iat", "iss", "sub", "token_use", "client_id"]

_jwk_clients: dict[str, jwt.PyJWKClient] = {}


class OperatorTokenError(Exception):
    """Raised when a bearer token is not a valid operator access token.

    :param reason: Short machine-readable reason for the rejection.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def bearer_token(headers: dict[str, str]) -> str:
    """Return the bearer token from an ``Authorization`` header, or ``""``.

    :param headers: Request headers with any key casing.
    :returns: The token after ``Bearer``, stripped, or an empty string.
    """
    for key, value in (headers or {}).items():
        if key.lower() == "authorization":
            scheme, _, token = str(value).partition(" ")
            if scheme.lower() == "bearer":
                return token.strip()
            return ""
    return ""


def user_pool_issuer(user_pool_id: str) -> str:
    """Return the Cognito issuer URL for a user pool id.

    :param user_pool_id: Pool id such as ``us-east-1_AbCdEf``.
    :returns: ``https://cognito-idp.<region>.amazonaws.com/<pool id>``.
    """
    region = user_pool_id.split("_", 1)[0]
    return f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"


def verify_operator_token(token: str) -> dict[str, Any]:
    """Verify a Cognito operator access token and return its claims.

    Reads ``USER_POOL_ID`` and ``ALLOWED_CLIENT_IDS`` (comma-separated)
    from the environment on every call.

    :param token: The raw JWT from the ``Authorization`` header.
    :returns: The verified token claims.
    :raises OperatorTokenError: If the token is missing, forged, expired,
        not an access token, issued to another client, or if the verifier
        is not configured.
    """
    user_pool_id = os.environ.get("USER_POOL_ID", "").strip()
    allowed_client_ids = {
        client_id.strip()
        for client_id in os.environ.get("ALLOWED_CLIENT_IDS", "").split(",")
        if client_id.strip()
    }
    if not user_pool_id or not allowed_client_ids:
        raise OperatorTokenError("verifier_not_configured")
    if not token:
        raise OperatorTokenError("missing_bearer")

    issuer = user_pool_issuer(user_pool_id)
    try:
        signing_key = _jwk_client(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"require": REQUIRED_CLAIMS, "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise OperatorTokenError("token_expired") from exc
    except jwt.PyJWTError as exc:
        raise OperatorTokenError("invalid_token") from exc

    if claims.get("token_use") != "access":
        raise OperatorTokenError("not_an_access_token")
    if claims.get("client_id") not in allowed_client_ids:
        raise OperatorTokenError("client_not_allowed")
    return claims


def _jwk_client(issuer: str) -> jwt.PyJWKClient:
    """Return the cached JWKS client for an issuer.

    :param issuer: The user pool issuer URL.
    :returns: A key-caching :class:`jwt.PyJWKClient` for that pool's JWKS.
    """
    client = _jwk_clients.get(issuer)
    if client is None:
        client = jwt.PyJWKClient(
            f"{issuer}/.well-known/jwks.json", cache_keys=True, timeout=5
        )
        _jwk_clients[issuer] = client
    return client
