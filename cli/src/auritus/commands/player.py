"""auritus player helper command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from auritus.embed import format_embed_snippet, verify_embed_snippet

app = typer.Typer(help="Print or verify an embed snippet.")


@app.callback(invoke_without_command=True)
def player(
    ctx: typer.Context,
    site_key: Optional[str] = typer.Option(
        None, "--site-key", help="Site key (required when printing a snippet)."
    ),
    name: str = typer.Option("", "--name", help="Clip name"),
    byline: str = typer.Option("", "--byline", help="Clip byline"),
    script_src: str = typer.Option(
        "https://aurit.us/embed.js", "--script-src", help="Embed script URL"
    ),
) -> None:
    """Print a ready-to-paste embed snippet when no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    if not site_key:
        typer.secho(
            "--site-key is required to print a snippet.", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1)
    typer.echo(
        format_embed_snippet(
            site_key=site_key,
            name=name,
            byline=byline,
            script_src=script_src,
        )
    )


@app.command("verify")
def verify(
    snippet: str = typer.Argument(
        "",
        help="Snippet text to verify (or use --file).",
    ),
    file: Path | None = typer.Option(
        None,
        "--file",
        exists=True,
        dir_okay=False,
        help="Read snippet from a file.",
    ),
) -> None:
    """Verify that an embed snippet includes a non-empty site key."""
    text = snippet
    if file is not None:
        text = file.read_text(encoding="utf-8")
    if not text.strip():
        typer.secho("Provide snippet text or --file.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    ok, message = verify_embed_snippet(text)
    if not ok:
        typer.secho(message, fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    typer.secho(message, fg=typer.colors.GREEN)
