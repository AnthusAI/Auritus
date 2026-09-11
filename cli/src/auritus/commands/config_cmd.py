"""auritus config command."""

from __future__ import annotations

import json
from typing import Any

import typer

from auritus.config import load_config, save_config

app = typer.Typer(help="Show or edit Auritus config (global or ./.auritus/config).")


@app.command("show")
def show(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON."),
) -> None:
    """Print the current configuration."""
    cfg = load_config()
    if as_json:
        typer.echo(json.dumps(cfg, indent=2, sort_keys=True))
        return
    for key, value in cfg.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                typer.echo(f"{key}.{nested_key}={nested_value}")
        else:
            typer.echo(f"{key}={value}")


@app.command("set")
def set_value(
    key: str = typer.Argument(
        ..., help="Config key, e.g. api_endpoint or worker.tts_backend"
    ),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value."""
    cfg = load_config()
    if "." in key:
        section, nested = key.split(".", 1)
        if section not in cfg or not isinstance(cfg[section], dict):
            cfg[section] = {}
        cfg[section][nested] = _coerce(value)
    else:
        cfg[key] = _coerce(value)
    path = save_config(cfg)
    typer.echo(f"Wrote {path}")


def _coerce(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        return int(value)
    except ValueError:
        return value
