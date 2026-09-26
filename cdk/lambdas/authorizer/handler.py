"""API Gateway HTTP API Lambda authorizer for Auritus operator routes.

Admits a request only when its bearer token is a Cognito access token that
``auritus_operator_auth`` verifies: RS256 signature against the user pool
JWKS, exact issuer, unexpired, ``token_use`` of ``access``, and a
``client_id`` from ``ALLOWED_CLIENT_IDS``.
"""

from __future__ import annotations

from typing import Any

from auritus_operator_auth import (
    OperatorTokenError,
    bearer_token,
    verify_operator_token,
)


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Authorize an operator request by verifying its Cognito access token.

    :param event: API Gateway authorizer event (HTTP API payload 2.0).
    :param _context: Lambda context (unused).
    :returns: Simple response authorizer document with ``isAuthorized``.
    """
    try:
        claims = verify_operator_token(bearer_token(event.get("headers") or {}))
    except OperatorTokenError as exc:
        return {"isAuthorized": False, "context": {"reason": exc.reason}}
    return {
        "isAuthorized": True,
        "context": {
            "sub": str(claims["sub"]),
            "routeArn": event.get("routeArn") or "*",
        },
    }
