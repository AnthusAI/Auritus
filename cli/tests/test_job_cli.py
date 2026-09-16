"""Tests for the `auritus job` list/show/delete/regenerate/retry CLI output and UX."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from auritus.api import AuritusApiError
from auritus.cli import app

runner = CliRunner()


def test_job_list_prints_real_field_values() -> None:
    """GET /admin/jobs returns rows shaped {content_hash, status, tts_backend, ...}."""
    fake_client = MagicMock()
    fake_client.list_jobs.return_value = {
        "jobs": [
            {
                "content_hash": "abc123",
                "status": "completed",
                "tts_backend": "kokoro",
                "voice_id": "default",
                "text": "Hello world",
                "name": "clip1",
                "byline": "author",
                "site_id": "site-1",
                "worker_type": "batch",
                "claimed_by": "worker-1",
                "created_at": "2026-09-14T00:00:00Z",
                "claimed_at": "2026-09-14T00:01:00Z",
                "completed_at": "2026-09-14T00:02:00Z",
                "failed_at": None,
                "duration_seconds": 2,
                "error_message": None,
                "audio_url": "https://example.com/audio.wav",
            },
            {
                "content_hash": "def456",
                "status": "pending",
                "tts_backend": "kokoro",
                "voice_id": "default",
                "text": "Another clip",
                "name": "clip2",
                "byline": "author",
                "site_id": "site-2",
                "worker_type": "batch",
                "claimed_by": None,
                "created_at": "2026-09-15T00:00:00Z",
                "claimed_at": None,
                "completed_at": None,
                "failed_at": None,
                "duration_seconds": None,
                "error_message": None,
                "audio_url": None,
            },
        ],
        "next_token": None,
    }
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "list"])
    assert result.exit_code == 0, result.output
    assert "abc123" in result.output
    assert "status=completed" in result.output
    assert "backend=kokoro" in result.output
    assert "def456" in result.output
    assert "status=pending" in result.output


def test_job_list_with_status_filter() -> None:
    """job list --status pending should pass status to api.list_jobs()."""
    fake_client = MagicMock()
    fake_client.list_jobs.return_value = {"jobs": [], "next_token": None}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "list", "--status", "pending"])
    assert result.exit_code == 0, result.output
    fake_client.list_jobs.assert_called_once_with(status="pending", limit=25)


def test_job_list_with_limit() -> None:
    """job list --limit N should pass limit to api.list_jobs()."""
    fake_client = MagicMock()
    fake_client.list_jobs.return_value = {"jobs": [], "next_token": None}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "list", "--limit", "10"])
    assert result.exit_code == 0, result.output
    fake_client.list_jobs.assert_called_once_with(status=None, limit=10)


def test_job_list_empty() -> None:
    """Listing with no jobs should print (no jobs)."""
    fake_client = MagicMock()
    fake_client.list_jobs.return_value = {"jobs": [], "next_token": None}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "list"])
    assert result.exit_code == 0, result.output
    assert "(no jobs)" in result.output


def test_job_show_prints_all_fields() -> None:
    """GET /admin/jobs/{hash} returns full job telemetry including site_key."""
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
    }
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "show", "--hash", "abc123"])
    assert result.exit_code == 0, result.output
    fake_client.get_admin_job.assert_called_once_with("abc123")
    assert "content_hash=abc123" in result.output
    assert "status=completed" in result.output
    assert "site_key=sk-secret" in result.output


def test_job_delete_with_yes_flag() -> None:
    """job delete --hash ... --yes should delete without prompting."""
    fake_client = MagicMock()
    fake_client.delete_job.return_value = {}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "delete", "--hash", "abc123", "--yes"])
    assert result.exit_code == 0, result.output
    fake_client.delete_job.assert_called_once_with("abc123")
    assert "Deleted abc123" in result.output


def test_job_delete_without_yes_prompts_user() -> None:
    """job delete without --yes should prompt user for confirmation."""
    fake_client = MagicMock()
    fake_client.delete_job.return_value = {}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "delete", "--hash", "abc123"], input="y\n")
    assert result.exit_code == 0, result.output
    fake_client.delete_job.assert_called_once_with("abc123")
    assert "Deleted abc123" in result.output


def test_job_delete_without_yes_respects_no_confirmation() -> None:
    """job delete without --yes and user says no should not delete."""
    fake_client = MagicMock()
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "delete", "--hash", "abc123"], input="\n")
    assert result.exit_code == 0, result.output
    fake_client.delete_job.assert_not_called()


def test_job_regenerate_calls_api() -> None:
    """job regenerate should call client.regenerate_job()."""
    fake_client = MagicMock()
    fake_client.regenerate_job.return_value = {}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "regenerate", "--hash", "abc123"])
    assert result.exit_code == 0, result.output
    fake_client.regenerate_job.assert_called_once_with("abc123")
    assert "Regeneration started for abc123" in result.output


def test_job_retry_calls_api_without_force() -> None:
    """job retry without --force should call client.retry_job(force=False)."""
    fake_client = MagicMock()
    fake_client.retry_job.return_value = {}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "retry", "--hash", "abc123"])
    assert result.exit_code == 0, result.output
    fake_client.retry_job.assert_called_once_with("abc123", force=False)
    assert "Retry started for abc123" in result.output


def test_job_retry_calls_api_with_force() -> None:
    """job retry --force should call client.retry_job(force=True)."""
    fake_client = MagicMock()
    fake_client.retry_job.return_value = {}
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "retry", "--hash", "abc123", "--force"])
    assert result.exit_code == 0, result.output
    fake_client.retry_job.assert_called_once_with("abc123", force=True)
    assert "Retry started for abc123" in result.output


def test_job_list_api_error_prints_to_stderr() -> None:
    """API errors should print to stderr in red and exit 1."""
    fake_client = MagicMock()
    fake_client.list_jobs.side_effect = AuritusApiError(
        "GET /admin/jobs failed: 401 Unauthorized"
    )
    with patch("auritus.commands.job.AuritusClient", return_value=fake_client):
        result = runner.invoke(app, ["job", "list"])
    assert result.exit_code == 1
    assert "GET /admin/jobs failed: 401 Unauthorized" in result.output


def test_job_list_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["job", "list", "--help"])
    assert result.exit_code == 0, result.output


def test_job_show_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["job", "show", "--help"])
    assert result.exit_code == 0, result.output


def test_job_delete_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["job", "delete", "--help"])
    assert result.exit_code == 0, result.output


def test_job_regenerate_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["job", "regenerate", "--help"])
    assert result.exit_code == 0, result.output


def test_job_retry_help_does_not_crash() -> None:
    """Regression: --help should not crash."""
    result = runner.invoke(app, ["job", "retry", "--help"])
    assert result.exit_code == 0, result.output
