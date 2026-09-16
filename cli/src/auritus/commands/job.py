"""auritus job list/show/delete/regenerate/retry commands."""

from __future__ import annotations

import typer

from auritus.api import AuritusApiError, AuritusClient

app = typer.Typer(help="Inspect and manage generation jobs.")


@app.command("list")
def list_jobs(
    status: str | None = typer.Option(None, "--status", help="Filter by job status."),
    limit: int = typer.Option(25, "--limit", help="Maximum jobs to return."),
) -> None:
    """List recent jobs."""
    try:
        client = AuritusClient()
        result = client.list_jobs(status=status, limit=limit)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    jobs = result.get("jobs") or []
    if not jobs:
        typer.echo("(no jobs)")
        return
    for job in jobs:
        typer.echo(
            f"{job.get('content_hash')}\tstatus={job.get('status')}\t"
            f"backend={job.get('tts_backend')}\tcreated_at={job.get('created_at')}"
        )


@app.command("show")
def show_job(
    content_hash: str = typer.Option(..., "--hash", help="Job content hash."),
) -> None:
    """Show full details for one job."""
    try:
        client = AuritusClient()
        job = client.get_admin_job(content_hash)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    for key, value in job.items():
        typer.echo(f"{key}={value}")


@app.command("delete")
def delete_job(
    content_hash: str = typer.Option(..., "--hash", help="Job content hash."),
    yes: bool = typer.Option(
        False, "--yes", help="Skip confirmation.", flag_value=True
    ),
) -> None:
    """Delete a job and its audio artifact."""
    if not yes and not typer.confirm(f"Delete job {content_hash}?"):
        raise typer.Exit(code=0)
    try:
        client = AuritusClient()
        client.delete_job(content_hash)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Deleted {content_hash}", fg=typer.colors.GREEN)


@app.command("regenerate")
def regenerate_job(
    content_hash: str = typer.Option(..., "--hash", help="Job content hash."),
) -> None:
    """Force regeneration of a job, even if content is unchanged."""
    try:
        client = AuritusClient()
        client.regenerate_job(content_hash)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Regeneration started for {content_hash}", fg=typer.colors.GREEN)


@app.command("retry")
def retry_job(
    content_hash: str = typer.Option(..., "--hash", help="Job content hash."),
    force: bool = typer.Option(
        False,
        "--force",
        help="Release a live claim, not just a stale one.",
        flag_value=True,
    ),
) -> None:
    """Retry a failed job, or release a stuck claim."""
    try:
        client = AuritusClient()
        client.retry_job(content_hash, force=force)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Retry started for {content_hash}", fg=typer.colors.GREEN)
