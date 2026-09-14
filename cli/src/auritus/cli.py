"""Auritus command-line interface."""

from __future__ import annotations

import click.core
import typer

from auritus.commands import config_cmd, worker_cmd
from auritus.commands import deploy as deploy_cmd
from auritus.commands import killswitch as killswitch_cmd
from auritus.commands import login as login_cmd
from auritus.commands import player as player_cmd
from auritus.commands import site as site_cmd
from auritus.commands.login import logout_cmd

# Compatibility bridge for Click 8.2+ signature change in make_metavar
_orig_make_metavar = click.core.Parameter.make_metavar


def _compat_make_metavar(
    self: click.core.Parameter, ctx: click.Context | None = None
) -> str:
    if ctx is None:
        ctx = click.get_current_context(silent=True)
    return _orig_make_metavar(self, ctx)  # type: ignore[arg-type]


click.core.Parameter.make_metavar = _compat_make_metavar  # type: ignore[method-assign]

app = typer.Typer(
    name="auritus",
    help="Auritus: open just-in-time TTS embed for web pages.",
    no_args_is_help=True,
)

app.add_typer(login_cmd.app, name="login")
app.command(
    name="logout", help="Revoke the cached refresh token and clear credentials."
)(logout_cmd)
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
