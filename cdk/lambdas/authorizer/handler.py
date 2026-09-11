"""API Gateway HTTP API Lambda authorizer for Auritus operator routes."""

from __future__ import annotations

import json
import os
from typing import Any

USER_POOL_ID = os.environ.get("USER_POOL_ID", "")
CLIENT_ID = os.environ.get("CLIENT_ID", "")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Authorize operator requests using a Bearer JWT shape check.

    Full JWKS signature verification against the Cognito user pool should be
    added here (fetch ``/.well-known/jwks.json``, validate ``iss``, ``aud``,
    ``exp``, and RS256 signature). This stub only enforces header presence and
    JWT structure so local stacks can deploy before JWKS wiring is complete.

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
    parts = token.split(".")
    if len(parts) != 3:
        return _deny("invalid_jwt_shape")

    try:
        header = _decode_segment(parts[0])
        payload = _decode_segment(parts[1])
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _deny("invalid_jwt_encoding")

    if header.get("alg") not in ("RS256", "RS384", "RS512"):
        return _deny("unsupported_alg")

    if USER_POOL_ID and USER_POOL_ID not in str(payload.get("iss", "")):
        return _deny("issuer_mismatch")

    audience = payload.get("aud") or payload.get("client_id")
    if CLIENT_ID and audience != CLIENT_ID:
        return _deny("audience_mismatch")

    route_arn = event.get("routeArn") or event.get("methodArn") or "*"
    return {
        "isAuthorized": True,
        "context": {
            "sub": str(payload.get("sub", "")),
            "routeArn": route_arn,
        },
    }


def _deny(reason: str) -> dict[str, Any]:
    return {"isAuthorized": False, "context": {"reason": reason}}


def _decode_segment(segment: str) -> dict[str, Any]:
    import base64

    padded = segment + "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))
