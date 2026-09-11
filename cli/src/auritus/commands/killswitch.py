"""auritus killswitch command for Batch spend guardrails."""

from __future__ import annotations

import typer

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from auritus.api import AuritusApiError, AuritusClient
from auritus.config import load_config

app = typer.Typer(help="Disable or re-enable the AWS Batch job queue.")


def _batch_queue_state(enabled: bool) -> None:
    """Toggle the configured Batch queue via AWS when the API is unavailable."""
    cfg = load_config()
    queue = str(cfg.get("batch_queue") or "").strip()
    region = str(cfg.get("region") or "us-east-1")
    if not queue:
        raise AuritusApiError(
            "batch_queue is not set in config and the API kill-switch failed."
        )
    state = "ENABLED" if enabled else "DISABLED"
    try:
        client = boto3.client("batch", region_name=region)
        client.update_job_queue(jobQueue=queue, state=state)
    except (BotoCoreError, ClientError) as exc:
        raise AuritusApiError(f"AWS Batch update failed: {exc}") from exc
    typer.secho(f"Batch queue {queue} set to {state} via AWS.", fg=typer.colors.YELLOW)


@app.command("disable")
def disable() -> None:
    """Disable the Batch queue (emergency spend stop)."""
    try:
        client = AuritusClient()
        result = client.disable_batch_queue()
        typer.secho(f"Batch queue disabled: {result}", fg=typer.colors.YELLOW)
    except AuritusApiError as exc:
        typer.secho(
            f"API kill-switch failed ({exc}); trying AWS.", fg=typer.colors.YELLOW
        )
        try:
            _batch_queue_state(False)
        except AuritusApiError as aws_exc:
            typer.secho(str(aws_exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from aws_exc


@app.command("enable")
def enable() -> None:
    """Re-enable the Batch queue after a kill-switch."""
    try:
        client = AuritusClient()
        result = client.enable_batch_queue()
        typer.secho(f"Batch queue enabled: {result}", fg=typer.colors.GREEN)
    except AuritusApiError as exc:
        typer.secho(
            f"API kill-switch failed ({exc}); trying AWS.", fg=typer.colors.YELLOW
        )
        try:
            _batch_queue_state(True)
        except AuritusApiError as aws_exc:
            typer.secho(str(aws_exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from aws_exc
