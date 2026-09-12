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
    """Authorize operator requests by verifying a Cognito JWT.

    :param event: API Gateway authorizer event (HTTP API payload 2.0).
    :param _context: Lambda context (unused).
    :returns: Simple response authorizer document with ``isAuthorized``.
    """
    headers = event.get("headers") or {}
    auth = next(
        (value for key, value in headers.items() if key.lower() == "authorization"), ""
    )
    if not auth.lower().startswith("bearer "):
        return _deny("missing_bearer")

    token = auth.split(" ", 1)[1].strip()
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        issuer = str(unverified["iss"])
        if USER_POOL_ID and USER_POOL_ID not in issuer:
            return _deny("issuer_mismatch")
        jwks = _jwks_cache.get(issuer)
        if jwks is None:
            with urllib.request.urlopen(f"{issuer}/.well-known/jwks.json") as response:
                jwks = json.loads(response.read())
            _jwks_cache[issuer] = jwks
        kid = jwt.get_unverified_header(token)["kid"]
        key = next(key for key in jwks["keys"] if key["kid"] == kid)
        payload = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key)),
            algorithms=["RS256"],
            issuer=issuer,
            audience=CLIENT_ID,
        )
    except (KeyError, StopIteration, ValueError, TypeError, jwt.PyJWTError, OSError):
        return _deny("invalid_token")

    route_arn = event.get("routeArn") or event.get("methodArn") or "*"
    return {
        "isAuthorized": True,
        "context": {"sub": str(payload.get("sub", "")), "routeArn": route_arn},
    }


def _deny(reason: str) -> dict[str, Any]:
    """Build a deny response with a reason.

    :param reason: Why the request is denied.
    :returns: Authorizer response with ``isAuthorized`` set to False.
    """
    return {"isAuthorized": False, "context": {"reason": reason}}
