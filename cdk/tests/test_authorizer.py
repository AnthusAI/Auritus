"""Acceptance tests for the Cognito JWT authorizer."""

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


def test_authorizes_signed_token_and_denies_tampering():
    """Signed tokens authorize while tampered tokens are denied."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    )
    public_jwk["kid"] = "test-key"
    issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-test"
    authorizer.CLIENT_ID = "client"
    authorizer._jwks_cache.clear()
    token = jwt.encode(
        {"iss": issuer, "aud": "client", "sub": "subject", "exp": 4102444800},
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    jwks = {"keys": [public_jwk]}
    event = {"headers": {"authorization": f"Bearer {token}"}}
    with patch.object(authorizer.urllib.request, "urlopen") as fetch:
        fetch.return_value.__enter__.return_value.read.return_value = json.dumps(
            jwks
        ).encode()
        fetch.return_value.__enter__.return_value.__iter__ = lambda _: iter([])
        fetch.return_value.__enter__.return_value = type(
            "Response",
            (),
            {"read": lambda self: json.dumps(jwks).encode()},
        )()
        assert authorizer.handler(event, None)["isAuthorized"] is True
    tampered = f"{token[:-1]}{'a' if token[-1] != 'a' else 'b'}"
    assert (
        authorizer.handler({"headers": {"authorization": f"Bearer {tampered}"}}, None)[
            "isAuthorized"
        ]
        is False
    )
