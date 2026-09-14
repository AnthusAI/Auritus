"""auritus login command."""

from __future__ import annotations

import typer

from auritus.auth import AuthError, login_with_password, login_with_sso, revoke_tokens

app = typer.Typer(
    help="Authenticate with Cognito using email/password or SSO (Google / AWS IAM Identity Center)."
)


@app.callback(invoke_without_command=True)
def login(
    username: str | None = typer.Option(
        None,
        "--username",
        help="Cognito user email for native pool password authentication.",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        help="Cognito password; prompted securely when omitted.",
    ),
    sso: str | None = typer.Option(
        None,
        "--sso",
        help="Authenticate via SSO: 'google' or 'aws-sso' (IAM Identity Center).",
    ),
) -> None:
    """Log in with Cognito email/password or SSO (Google / AWS IAM Identity Center). Caches short-lived JWTs."""
    if sso:
        provider_map = {
            "google": "Google",
            "aws-sso": "IdentityCenter",
            "identity-center": "IdentityCenter",
        }
        provider = provider_map.get(sso.lower())
        if not provider:
            typer.secho(
                f"Unknown SSO provider: {sso}. Choose 'google' or 'aws-sso'.",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=1)
        try:
            tokens = login_with_sso(provider)
        except AuthError as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc
        typer.secho(f"Logged in via {provider} SSO.", fg=typer.colors.GREEN)
        expires = tokens.get("expires_in")
        if expires:
            typer.echo(f"Access token expires in {expires} seconds.")
        return

    if not username:
        username = typer.prompt("Username (email)")

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


def logout_cmd() -> None:
    """Revoke the cached Cognito refresh token and clear local credentials."""
    try:
        revoke_tokens()
    except AuthError as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW, err=True)
    typer.secho("Logged out.", fg=typer.colors.GREEN)
