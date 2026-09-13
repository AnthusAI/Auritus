"""auritus worker command (local GPU daemon)."""

from __future__ import annotations

import typer

from auritus.worker.daemon import run_worker


def register(app: typer.Typer) -> None:
    """Attach ``worker`` as a top-level command (avoids Typer callback Option quirks)."""

    @app.command("worker")
    def worker(
        once: bool = typer.Option(
            False,
            "--once",
            help="Claim and process at most one job",
            flag_value=True,
        ),
    ) -> None:
        """Poll claimable jobs, claim via mutex, generate TTS locally, upload, mark done."""
        run_worker(once=bool(once))
