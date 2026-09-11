"""API Gateway HTTP API Lambda authorizer for Auritus operator routes."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import jwt

USER_POOL_ID = os.environ.get("USER_POOL_ID", "")
CLIENT_ID = os.environ.get("CLIENT_ID", "")
_jwks_cache: dict[str, dict[str, Any]] = {}


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Authorize operator requests using Cognito JWKS signature verification.

    :param event: API Gateway authorizer event (HTTP API payload 2.0).
    :param _context: Lambda context (unused).
    :returns: Simple response authorizer document with ``isAuthorized``.
    """
    headers = event.get("headers") or {}
    auth = ""
    for key, value in headers.items():
        if key.lower() == "authorization":
            auth = value
            break

    if not auth.lower().startswith("bearer "):
        return _deny("missing_bearer")

    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        issuer = str(payload["iss"])
        jwks = _get_jwks(issuer)
        header = jwt.get_unverified_header(token)
        jwk = next(jwk for jwk in jwks["keys"] if jwk.get("kid") == header["kid"])
        key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        payload = jwt.decode(
            token, key, algorithms=["RS256"], audience=CLIENT_ID, issuer=issuer
        )
    except (
        jwt.exceptions.InvalidTokenError,
        KeyError,
        StopIteration,
        ValueError,
    ) as exc:
        return _deny(str(exc))

    route_arn = event.get("routeArn") or event.get("methodArn") or "*"
    return {
        "isAuthorized": True,
        "context": {
            "sub": str(payload.get("sub", "")),
            "routeArn": route_arn,
        },
    }


def _get_jwks(issuer: str) -> dict[str, Any]:
    if issuer not in _jwks_cache:
        with urllib.request.urlopen(
            f"{issuer}/.well-known/jwks.json", timeout=5
        ) as response:
            _jwks_cache[issuer] = json.load(response)
    return _jwks_cache[issuer]


def _deny(reason: str) -> dict[str, Any]:
    return {"isAuthorized": False, "context": {"reason": reason}}
