"""Tests for the `auritus cost` CLI output and UX."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from auritus.api import AuritusApiError
from auritus.cli import app

runner = CliRunner()


def test_cost_summary_prints_total_with_separate_lines() -> None:
    """Default cost invocation prints total GPU/platform/avoided costs as separate lines."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [],
        "total": {
            "gpu_cost_usd": Decimal("123.4567"),
            "platform_cost_usd": Decimal("45.6789"),
            "avoided_cost_usd": Decimal("10.1234"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0, result.output
    assert "GPU Cost: $123.4567" in result.output
    assert "Platform Cost: $45.6789" in result.output
    assert "Avoided Cost: $10.1234" in result.output
    assert "modelled cost estimates" in result.output


def test_cost_summary_formats_to_four_decimal_places() -> None:
    """Cost amounts must be formatted to exactly 4 decimal places."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [],
        "total": {
            "gpu_cost_usd": Decimal("0.123456"),
            "platform_cost_usd": Decimal("5.00"),
            "avoided_cost_usd": Decimal("0.001"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0, result.output
    # Verify exact 4-decimal formatting
    assert "$0.1235" in result.output  # rounded
    assert "$5.0000" in result.output
    assert "$0.0010" in result.output


def test_cost_summary_with_site_filter() -> None:
    """cost --site should pass site_id to client.get_costs()."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [],
        "total": {
            "gpu_cost_usd": Decimal("10"),
            "platform_cost_usd": Decimal("5"),
            "avoided_cost_usd": Decimal("2"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost", "--site", "site-123"])
    assert result.exit_code == 0, result.output
    fake_client.get_costs.assert_called_once_with(
        site_id="site-123", from_date=None, to_date=None
    )


def test_cost_summary_with_date_range() -> None:
    """cost --from and --to should pass date filters to client.get_costs()."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [],
        "total": {
            "gpu_cost_usd": Decimal("10"),
            "platform_cost_usd": Decimal("5"),
            "avoided_cost_usd": Decimal("2"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(
            app, ["cost", "--from", "2026-01-01", "--to", "2026-01-31"]
        )
    assert result.exit_code == 0, result.output
    fake_client.get_costs.assert_called_once_with(
        site_id=None, from_date="2026-01-01", to_date="2026-01-31"
    )


def test_cost_daily_prints_one_row_per_day() -> None:
    """cost --daily should print a row for each day in the daily array."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [
            {
                "site_id": "site-1",
                "date": "2026-09-14",
                "gpu_cost_usd": Decimal("10.1234"),
                "platform_cost_usd": Decimal("5.5678"),
                "avoided_cost_usd": Decimal("2.0000"),
                "batch_job_count": 5,
                "local_job_count": 3,
            },
            {
                "site_id": "site-1",
                "date": "2026-09-15",
                "gpu_cost_usd": Decimal("15.9999"),
                "platform_cost_usd": Decimal("7.0001"),
                "avoided_cost_usd": Decimal("1.5000"),
                "batch_job_count": 8,
                "local_job_count": 2,
            },
        ],
        "total": {
            "gpu_cost_usd": Decimal("26.1233"),
            "platform_cost_usd": Decimal("12.5679"),
            "avoided_cost_usd": Decimal("3.5000"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost", "--daily"])
    assert result.exit_code == 0, result.output
    # Check for daily row headers
    assert "2026-09-14" in result.output
    assert "2026-09-15" in result.output
    # Values are aligned in the table output
    assert "10.1234" in result.output
    assert "15.9999" in result.output
    # Check job counts are summed
    assert "8" in result.output  # 5 + 3 for first day
    assert "10" in result.output  # 8 + 2 for second day


def test_cost_empty_result_prints_message() -> None:
    """Empty cost data should print a sensible message, not a crash or wall of zeros."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {"daily": [], "total": {}}
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost"])
    assert result.exit_code == 0, result.output
    assert "No cost data for this range" in result.output


def test_cost_with_all_filters() -> None:
    """Combining all filters should pass them all to client.get_costs()."""
    fake_client = MagicMock()
    fake_client.get_costs.return_value = {
        "daily": [],
        "total": {
            "gpu_cost_usd": Decimal("10"),
            "platform_cost_usd": Decimal("5"),
            "avoided_cost_usd": Decimal("2"),
        },
    }
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(
            app,
            [
                "cost",
                "--site",
                "site-xyz",
                "--from",
                "2026-01-15",
                "--to",
                "2026-02-15",
            ],
        )
    assert result.exit_code == 0, result.output
    fake_client.get_costs.assert_called_once_with(
        site_id="site-xyz", from_date="2026-01-15", to_date="2026-02-15"
    )


def test_cost_api_error_prints_to_stderr() -> None:
    """API errors should print to stderr in red and exit 1."""
    fake_client = MagicMock()
    fake_client.get_costs.side_effect = AuritusApiError(
        "GET /admin/costs failed: 401 Unauthorized"
    )
    with patch("auritus.commands.cost.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["cost"])
    assert result.exit_code == 1
    assert "GET /admin/costs failed: 401 Unauthorized" in result.output


def test_cost_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["cost", "--help"])
    assert result.exit_code == 0, result.output


def test_cost_daily_help_does_not_crash() -> None:
    """Regression: --daily --help should not crash."""
    result = runner.invoke(app, ["cost", "--daily", "--help"])
    assert result.exit_code == 0, result.output


def test_job_show_includes_cost_fields() -> None:
    """job show should include formatted cost fields when present."""
    fake_client = MagicMock()
    fake_client.get_admin_job.return_value = {
        "content_hash": "abc123",
        "status": "completed",
        "tts_backend": "kokoro",
        "voice_id": "default",
        "text": "Hello world",
        "name": "clip1",
        "byline": "author",
        "site_id": "site-1",
        "site_key": "sk-secret",
        "worker_type": "batch",
        "claimed_by": "worker-1",
        "created_at": "2026-09-14T00:00:00Z",
        "claimed_at": "2026-09-14T00:01:00Z",
        "completed_at": "2026-09-14T00:02:00Z",
        "failed_at": None,
        "duration_seconds": 2,
        "error_message": None,
        "audio_url": "https://example.com/audio.wav",
        "gpu_cost_usd": Decimal("5.1234"),
        "platform_cost_usd": Decimal("2.0000"),
        "cost_rate_usd_per_hour": Decimal("0.5678"),
        "rate_card_version": "v1",
        "avoided_cost_usd": Decimal("0.0000"),
        "avoided_cost_basis": "batch_job",
    }
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "show", "--hash", "abc123"])
    assert result.exit_code == 0, result.output
    assert "gpu_cost_usd=5.1234" in result.output
    assert "platform_cost_usd=2.0000" in result.output
    assert "cost_rate_usd_per_hour=0.5678" in result.output


def test_job_show_omits_avoided_cost_for_batch_job() -> None:
    """job show should omit avoided_cost_usd when avoided_cost_basis is 'batch_job'."""
    fake_client = MagicMock()
    fake_client.get_admin_job.return_value = {
        "content_hash": "abc123",
        "status": "completed",
        "tts_backend": "kokoro",
        "voice_id": "default",
        "text": "Hello world",
        "name": "clip1",
        "byline": "author",
        "site_id": "site-1",
        "site_key": "sk-secret",
        "worker_type": "batch",
        "claimed_by": "worker-1",
        "created_at": "2026-09-14T00:00:00Z",
        "claimed_at": "2026-09-14T00:01:00Z",
        "completed_at": "2026-09-14T00:02:00Z",
        "failed_at": None,
        "duration_seconds": 2,
        "error_message": None,
        "audio_url": "https://example.com/audio.wav",
        "gpu_cost_usd": Decimal("5.1234"),
        "platform_cost_usd": Decimal("2.0000"),
        "cost_rate_usd_per_hour": Decimal("0.5678"),
        "rate_card_version": "v1",
        "avoided_cost_usd": Decimal("0.0000"),
        "avoided_cost_basis": "batch_job",
    }
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "show", "--hash", "abc123"])
    assert result.exit_code == 0, result.output
    # avoided_cost_usd should NOT be in the output for batch_job
    assert "avoided_cost_usd" not in result.output


def test_job_show_includes_avoided_cost_for_local_job() -> None:
    """job show should include avoided_cost_usd when avoided_cost_basis is not 'batch_job'."""
    fake_client = MagicMock()
    fake_client.get_admin_job.return_value = {
        "content_hash": "local123",
        "status": "completed",
        "tts_backend": "kokoro",
        "voice_id": "default",
        "text": "Hello world",
        "name": "clip1",
        "byline": "author",
        "site_id": "site-1",
        "site_key": "sk-secret",
        "worker_type": "local",
        "claimed_by": "worker-1",
        "created_at": "2026-09-14T00:00:00Z",
        "claimed_at": "2026-09-14T00:01:00Z",
        "completed_at": "2026-09-14T00:02:00Z",
        "failed_at": None,
        "duration_seconds": 2,
        "error_message": None,
        "audio_url": "https://example.com/audio.wav",
        "gpu_cost_usd": None,
        "platform_cost_usd": Decimal("2.0000"),
        "cost_rate_usd_per_hour": None,
        "rate_card_version": "v1",
        "avoided_cost_usd": Decimal("5.1234"),
        "avoided_cost_basis": "local",
    }
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "show", "--hash", "local123"])
    assert result.exit_code == 0, result.output
    # avoided_cost_usd SHOULD be in the output for local job
    assert "avoided_cost_usd=5.1234" in result.output
