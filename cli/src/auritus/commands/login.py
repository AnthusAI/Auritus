"""auritus login command."""

from __future__ import annotations

import typer

from auritus.auth import AuthError, login_interactive

app = typer.Typer(help="Authenticate with Cognito (Google OAuth).")


@app.callback(invoke_without_command=True)
def login(
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print the URL instead of opening a browser."
    ),
) -> None:
    """Log in via Google through Cognito. Caches short-lived JWTs."""
    try:
        tokens = login_interactive(open_browser=not no_browser)
    except AuthError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho("Logged in.", fg=typer.colors.GREEN)
    expires = tokens.get("expires_in")
    if expires:
        typer.echo(f"Access token expires in {expires} seconds.")
