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

# typer.core.TyperArgument carries its own make_metavar override (to render
# the argument name), used for Argument-based commands (e.g.
# `site revoke SITE_ID`). Its call signature has changed shape across the
# typer/click releases we've hit in this environment: typer's Rich help
# renderer calls it with no arguments at all, while Click's own usage
# formatter calls it as make_metavar(ctx) on some versions and
# make_metavar(ctx, usage=True/False) on others. An earlier fix here
# delegated to click.core.Argument.make_metavar (the plain base-class
# implementation) -- but that method's own signature is just (self), with
# no ctx or usage parameter at all in the click version installed today, so
# forwarding ctx/usage into it crashes just as hard as not patching at all.
# The actual fix is to delegate to TYPER's own make_metavar, captured here
# before we wrap it -- in every version seen so far it already knows how to
# render itself given a ctx and an optional usage flag; the only gap is the
# zero-argument call typer's Rich renderer makes, which we backfill with
# the current click context.
_orig_argument_make_metavar = typer.core.TyperArgument.make_metavar


def _compat_argument_make_metavar(
    self: click.core.Argument, *args: object, **kwargs: object
) -> str:
    if not args and "ctx" not in kwargs:
        args = (click.get_current_context(silent=True),)
    return _orig_argument_make_metavar(self, *args, **kwargs)  # type: ignore[arg-type]


typer.core.TyperArgument.make_metavar = _compat_argument_make_metavar  # type: ignore[method-assign]

# Compatibility bridge for Click 8.4+ UNSET flag_value with Typer
if hasattr(click.core, "UNSET"):
    _orig_option_init = click.Option.__init__

    def _compat_option_init(
        self: click.Option, *args: object, **kwargs: object
    ) -> None:
        if kwargs.get("flag_value") is None and kwargs.get("is_flag") is None:
            kwargs["flag_value"] = click.core.UNSET
        _orig_option_init(self, *args, **kwargs)  # type: ignore[arg-type]

    click.Option.__init__ = _compat_option_init  # type: ignore[method-assign]

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
