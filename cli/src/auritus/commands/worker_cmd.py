"""auritus worker command (local GPU daemon)."""

from __future__ import annotations

import typer

from auritus.worker.daemon import run_worker

app = typer.Typer(help="Run the local TTS worker daemon.")


@app.callback(invoke_without_command=True)
def worker(
    once: bool = typer.Option(
        False, "--once", help="Claim and process at most one job"
    ),
) -> None:
    """Poll claimable jobs, claim via mutex, generate TTS locally, upload, mark done."""
    run_worker(once=once)
