"""auritus login command."""

from __future__ import annotations

import typer

from auritus.auth import AuthError, login_with_password

app = typer.Typer(
    help="Authenticate with Cognito using email and password (not Google)."
)


@app.callback(invoke_without_command=True)
def login(
    username: str = typer.Option(
        ...,
        "--username",
        help="Cognito user email (native pool user, not Google sign-in).",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        help="Cognito password; prompted securely when omitted.",
    ),
) -> None:
    """Log in with Cognito email and password. Caches short-lived JWTs."""
    secret = password
    if secret is None:
        secret = typer.prompt("Password", hide_input=True)
    try:
        tokens = login_with_password(username, secret)
    except AuthError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho("Logged in.", fg=typer.colors.GREEN)
    expires = tokens.get("expires_in")
    if expires:
        typer.echo(f"Access token expires in {expires} seconds.")
