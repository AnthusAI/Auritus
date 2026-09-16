"""auritus site create/list/revoke commands."""

from __future__ import annotations

import typer

from auritus.api import AuritusApiError, AuritusClient
from auritus.embed import format_embed_snippet

app = typer.Typer(help="Manage site keys for embed snippets.")


@app.command("create")
def create(
    origin: str = typer.Option(..., "--origin", help="Allowed browser Origin"),
    name: str = typer.Option("", "--name", help="Human-readable site name"),
    clip_name: str = typer.Option("", "--clip-name", help="Default embed clip title"),
    byline: str = typer.Option("", "--byline", help="Default embed byline"),
) -> None:
    """Mint a site key and print the embed snippet."""
    try:
        client = AuritusClient()
        site = client.create_site(origin=origin, name=name)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    site_key = site.get("site_key") or site.get("key")
    typer.echo(f"site_id={site.get('site_id')}")
    typer.echo(f"site_key={site_key}")
    typer.echo(
        "(save site_key now -- it is not shown again; site_id is used to revoke)"
    )
    typer.echo("")
    typer.echo(
        format_embed_snippet(
            site_key=str(site_key),
            name=clip_name,
            byline=byline,
        )
    )


@app.command("list")
def list_sites() -> None:
    """List site keys."""
    try:
        client = AuritusClient()
        sites = client.list_sites()
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    if not sites:
        typer.echo("(no sites)")
        return
    # The API's GET /sites response only carries site_id/label/disabled/
    # created_at -- site_key is a secret shown once at `site create` time and
    # is never re-exposed by list, so it is intentionally not printed here.
    for site in sites:
        typer.echo(
            f"site_id={site.get('site_id')}\tlabel={site.get('label')}\t"
            f"disabled={site.get('disabled')}"
        )


@app.command("revoke")
def revoke(
    site_id: str = typer.Argument(
        ...,
        help=(
            "site_id to revoke, as printed by `site create` or `site list` "
            "(NOT the site_key used in embed snippets)."
        ),
    ),
) -> None:
    """Revoke a site key."""
    try:
        client = AuritusClient()
        client.revoke_site(site_id)
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(f"Revoked {site_id}", fg=typer.colors.GREEN)
