"""auritus cost command for viewing estimated and observed costs."""

from __future__ import annotations

from datetime import datetime

import typer

from auritus.api import AuritusApiError, AuritusClient

app = typer.Typer(help="View estimated job costs and local-worker savings.")


def _format_usd(value: float | int | None) -> str:
    """Format a USD amount to 4 decimal places."""
    if value is None:
        return "0.0000"
    return f"{float(value):.4f}"


@app.callback(invoke_without_command=True)
def cost_summary(
    ctx: typer.Context,
    site: str | None = typer.Option(None, "--site", help="Filter by site ID."),
    from_: str | None = typer.Option(
        None, "--from", help="Start date (YYYY-MM-DD), inclusive."
    ),
    to: str | None = typer.Option(
        None, "--to", help="End date (YYYY-MM-DD), inclusive."
    ),
    daily: bool = typer.Option(
        False, "--daily", help="Print one row per day.", flag_value=True
    ),
) -> None:
    """View cost summary and optional daily breakdown."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        client = AuritusClient()
        result = client.get_costs(site_id=site, from_date=from_, to_date=to)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    daily_data = result.get("daily") or []
    total = result.get("total") or {}

    # Handle empty result. The real API always returns `total` populated
    # with every cost field present (summed from `daily`, so all zero
    # when `daily` is empty) -- never an empty dict -- so a bare
    # `not total` check can never trigger against a real response. Treat
    # it as empty only when there is nothing to show either way: no
    # daily rows AND every total figure is zero (or `total` itself is
    # falsy, for a defensively-shaped response).
    no_cost_data = not daily_data and (
        not total or all((value or 0) == 0 for value in total.values())
    )
    if no_cost_data:
        typer.echo("No cost data for this range.")
        return

    # Print daily data if requested
    if daily:
        if daily_data:
            typer.echo(
                "Date            Site ID      GPU Cost    Platform Cost    Avoided Cost    Job Count"
            )
            typer.echo("-" * 85)
            for row in daily_data:
                date_str = row.get("date", "")
                site_id_str = row.get("site_id", "")
                gpu_cost = _format_usd(row.get("gpu_cost_usd"))
                plat_cost = _format_usd(row.get("platform_cost_usd"))
                avoided_cost = _format_usd(row.get("avoided_cost_usd"))
                job_count = (row.get("batch_job_count") or 0) + (
                    row.get("local_job_count") or 0
                )
                typer.echo(
                    f"{date_str:15} {site_id_str:12} ${gpu_cost:>10} ${plat_cost:>14} ${avoided_cost:>13} {job_count:>10}"
                )
        else:
            typer.echo("No daily cost data for this range.")

    # Print total summary
    typer.echo("")
    typer.echo("Cost Summary:")
    typer.echo(f"  GPU Cost: ${_format_usd(total.get('gpu_cost_usd'))}")
    typer.echo(f"  Platform Cost: ${_format_usd(total.get('platform_cost_usd'))}")
    typer.echo(f"  Avoided Cost: ${_format_usd(total.get('avoided_cost_usd'))}")
    typer.echo("")
    typer.echo("Note: These are modelled cost estimates, not an AWS invoice.")
