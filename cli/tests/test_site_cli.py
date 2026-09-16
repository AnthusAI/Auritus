"""Tests for the `auritus site` create/list/revoke CLI output and UX."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from auritus.cli import app

runner = CliRunner()


def test_site_create_prints_real_site_id_and_site_key() -> None:
    """POST /sites returns {site_id, site_key, label} -- create should print both."""
    fake_client = MagicMock()
    fake_client.create_site.return_value = {
        "site_id": "3d9b8b0e-1111-4c11-9a11-abc123456789",
        "site_key": "s3cr3t-token-value",
        "label": "my-site",
    }
    with patch("auritus.commands.site.AuritusClient", return_value=fake_client):
        result = runner.invoke(
            app, ["site", "create", "--origin", "https://example.com"]
        )
    assert result.exit_code == 0, result.output
    assert "site_id=3d9b8b0e-1111-4c11-9a11-abc123456789" in result.output
    assert "site_key=s3cr3t-token-value" in result.output
    assert "site_id=None" not in result.output


def test_site_list_prints_real_field_values() -> None:
    """GET /sites returns rows shaped {site_id, label, disabled, created_at}."""
    fake_client = MagicMock()
    fake_client.list_sites.return_value = [
        {
            "site_id": "aaa-111",
            "label": "pilobol.us",
            "disabled": False,
            "created_at": "2026-09-14T00:00:00Z",
        },
        {
            "site_id": "bbb-222",
            "label": "other-site",
            "disabled": True,
            "created_at": "2026-09-01T00:00:00Z",
        },
    ]
    with patch("auritus.commands.site.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["site", "list"])
    assert result.exit_code == 0, result.output
    assert "site_id=aaa-111" in result.output
    assert "label=pilobol.us" in result.output
    assert "disabled=False" in result.output
    assert "site_id=bbb-222" in result.output
    assert "None\torigin=None" not in result.output


def test_site_list_empty() -> None:
    fake_client = MagicMock()
    fake_client.list_sites.return_value = []
    with patch("auritus.commands.site.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["site", "list"])
    assert result.exit_code == 0, result.output
    assert "(no sites)" in result.output


def test_site_revoke_calls_api_with_site_id() -> None:
    fake_client = MagicMock()
    with patch("auritus.commands.site.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["site", "revoke", "aaa-111"])
    assert result.exit_code == 0, result.output
    fake_client.revoke_site.assert_called_once_with("aaa-111")


def test_site_revoke_help_does_not_crash() -> None:
    """Regression test: TyperArgument.make_metavar() version-mismatch crash.

    typer.core.TyperArgument.make_metavar's calling convention has shifted
    across the typer/click releases seen in this environment -- no
    arguments, a bare ctx, or ctx plus a usage keyword -- and each shift has
    crashed --help on any Argument-based command until auritus.cli's compat
    shim adapted to it. Assert only that --help renders without crashing and
    still documents the argument; the exact casing/braces typer chooses to
    render it with is a cosmetic detail this test should not pin down.
    """
    result = runner.invoke(app, ["site", "revoke", "--help"])
    assert result.exit_code == 0, result.output
    assert "site_id" in result.output.lower()


def test_site_create_help_does_not_crash() -> None:
    result = runner.invoke(app, ["site", "create", "--help"])
    assert result.exit_code == 0, result.output


def test_site_list_help_does_not_crash() -> None:
    result = runner.invoke(app, ["site", "list", "--help"])
    assert result.exit_code == 0, result.output
