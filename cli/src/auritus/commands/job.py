"""auritus job list/show/delete/regenerate/retry commands."""

from __future__ import annotations

import typer

from auritus.api import AuritusApiError, AuritusClient

app = typer.Typer(help="Inspect and manage generation jobs.")


@app.command("list")
def list_jobs(
    status: str | None = typer.Option(None, "--status", help="Filter by job status."),
    limit: int = typer.Option(25, "--limit", help="Maximum jobs to return."),
    next_token: str | None = typer.Option(
        None, "--next-token", help="Pagination cursor from a prior call."
    ),
) -> None:
    """List recent jobs."""
    try:
        client = AuritusClient()
        result = client.list_jobs(status=status, limit=limit, next_token=next_token)
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

    # Print pagination info if there are more results
    returned_next_token = result.get("next_token")
    if returned_next_token:
        typer.echo()
        typer.secho(
            f"Next page: auritus job list --next-token {returned_next_token}",
            fg=typer.colors.BLUE,
        )


def _format_cost_usd(value: float | int | None) -> str:
    """Format a USD cost amount to 4 decimal places."""
    if value is None:
        return "0.0000"
    return f"{float(value):.4f}"


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

    # Print all fields, with special formatting for cost fields
    cost_fields = {"gpu_cost_usd", "platform_cost_usd", "cost_rate_usd_per_hour"}
    for key, value in job.items():
        if key in cost_fields:
            formatted_value = _format_cost_usd(value)
            typer.echo(f"{key}={formatted_value}")
        elif key == "avoided_cost_usd":
            # Only print avoided_cost_usd when avoided_cost_basis is present and not "batch_job"
            avoided_basis = job.get("avoided_cost_basis")
            if avoided_basis and avoided_basis != "batch_job":
                formatted_value = _format_cost_usd(value)
                typer.echo(f"{key}={formatted_value}")
        else:
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


@app.command("purge")
def purge_jobs(
    site: str = typer.Option(None, "--site", help="Restrict to one site id."),
    status: str = typer.Option(None, "--status", help="Restrict to one job status."),
    older_than_days: int = typer.Option(
        None, "--older-than-days", help="Restrict to jobs older than this many days."
    ),
    yes: bool = typer.Option(
        False, "--yes", help="Skip the dry-run confirmation and actually delete."
    ),
) -> None:
    """Bulk-delete jobs matching a filter. Dry-run unless --yes is given."""
    if not site and not status and older_than_days is None:
        typer.secho(
            "At least one of --site, --status, or --older-than-days is required.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        client = AuritusClient()
        preview = client.bulk_delete_jobs(
            site_id=site,
            status=status,
            older_than_days=older_than_days,
            dry_run=True,
        )
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    matched = preview.get("matched", 0)
    typer.echo(f"{matched} job(s) match this filter.")

    if not yes:
        typer.echo("Re-run with --yes to delete them.")
        return

    if matched == 0:
        typer.echo("Nothing to delete.")
        return

    try:
        result = client.bulk_delete_jobs(
            site_id=site,
            status=status,
            older_than_days=older_than_days,
            dry_run=False,
        )
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Deleted {result.get('deleted', 0)} job(s).", fg=typer.colors.GREEN)


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
