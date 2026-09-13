"""Tests for the auritus worker CLI flag wiring."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from auritus.cli import app

runner = CliRunner()


def test_worker_without_once_passes_false() -> None:
    with patch("auritus.commands.worker_cmd.run_worker") as mock:
        result = runner.invoke(app, ["worker"])
    assert result.exit_code == 0
    mock.assert_called_once_with(once=False)


def test_worker_once_flag_passes_true() -> None:
    with patch("auritus.commands.worker_cmd.run_worker") as mock:
        result = runner.invoke(app, ["worker", "--once"])
    assert result.exit_code == 0
    mock.assert_called_once_with(once=True)
