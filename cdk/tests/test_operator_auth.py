"""Unit tests for the shared operator auth helpers outside the behave specs."""

from __future__ import annotations

import pytest
from support.operator_tokens import install_test_user_pool, operator_access_token

import auritus_operator_auth


def test_bearer_token_reads_authorization_header_in_any_case() -> None:
    """The bearer value is returned whatever the header and scheme casing."""
    assert auritus_operator_auth.bearer_token({"Authorization": "bearer abc"}) == "abc"
    assert (
        auritus_operator_auth.bearer_token({"authorization": "Bearer  abc "}) == "abc"
    )


def test_bearer_token_ignores_other_schemes_and_missing_header() -> None:
    """Non-bearer schemes and absent headers yield an empty token."""
    assert auritus_operator_auth.bearer_token({"authorization": "Basic abc"}) == ""
    assert auritus_operator_auth.bearer_token({}) == ""


def test_user_pool_issuer_uses_pool_region() -> None:
    """The issuer URL is derived from the region prefix of the pool id."""
    assert (
        auritus_operator_auth.user_pool_issuer("eu-west-2_Pool")
        == "https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_Pool"
    )


@pytest.mark.parametrize("unset_variable", ["USER_POOL_ID", "ALLOWED_CLIENT_IDS"])
def test_verifier_denies_every_token_when_not_configured(
    unset_variable: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing pool id or client allow-list fails closed."""
    token = operator_access_token()
    install_test_user_pool()
    monkeypatch.setenv(unset_variable, "")
    with pytest.raises(auritus_operator_auth.OperatorTokenError) as raised:
        auritus_operator_auth.verify_operator_token(token)
    assert raised.value.reason == "verifier_not_configured"


def test_verifier_returns_claims_for_valid_access_token() -> None:
    """A pool-signed access token for an allowed client verifies."""
    claims = auritus_operator_auth.verify_operator_token(operator_access_token())
    assert claims["token_use"] == "access"
