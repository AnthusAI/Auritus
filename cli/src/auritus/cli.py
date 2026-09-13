"""Auritus command-line interface."""

from __future__ import annotations

import typer

from auritus.commands import config_cmd, worker_cmd
from auritus.commands import deploy as deploy_cmd
from auritus.commands import killswitch as killswitch_cmd
from auritus.commands import login as login_cmd
from auritus.commands import player as player_cmd
from auritus.commands import site as site_cmd

app = typer.Typer(
    name="auritus",
    help="Auritus: open just-in-time TTS embed for web pages.",
    no_args_is_help=True,
)

app.add_typer(login_cmd.app, name="login")
app.add_typer(config_cmd.app, name="config")
app.add_typer(deploy_cmd.app, name="deploy")
app.add_typer(site_cmd.app, name="site")
app.add_typer(player_cmd.app, name="player")
worker_cmd.register(app)
app.add_typer(killswitch_cmd.app, name="killswitch")


@app.callback()
def main() -> None:
    """Auritus CLI entrypoint."""


if __name__ == "__main__":
    app()
