"""Configuration loader for ~/.auritus/config or ./.auritus/config (TOML)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

import tomli_w

DEFAULT_CLAIM_TIMEOUT_SECONDS = 900
DEFAULT_POLL_INTERVAL_SECONDS = 5
DEFAULT_TTS_BACKEND = "higgs"


def local_config_path() -> Path:
    """Return the project-local config path (may not exist)."""
    return Path.cwd() / ".auritus" / "config"


def config_dir() -> Path:
    """Return the global Auritus config directory under the user home."""
    return Path.home() / ".auritus"


def global_config_path() -> Path:
    """Return the global Auritus TOML config path."""
    return config_dir() / "config"


def config_path() -> Path:
    """Return the active config file path (local overrides global when present)."""
    local = local_config_path()
    if local.is_file():
        return local
    return global_config_path()


def default_config() -> dict[str, Any]:
    """Return the default configuration structure."""
    return {
        "api_endpoint": "",
        "region": "us-east-1",
        "cognito_client_id": "",
        "user_pool_id": "",
        "cognito_domain": "",
        "batch_queue": "",
        "s3_bucket": "",
        "cloudfront_domain": "",
        "worker": {
            "claim_timeout": DEFAULT_CLAIM_TIMEOUT_SECONDS,
            "poll_interval": DEFAULT_POLL_INTERVAL_SECONDS,
            "tts_backend": DEFAULT_TTS_BACKEND,
        },
    }


def load_config() -> dict[str, Any]:
    """Load configuration from disk, merging with defaults."""
    path = config_path()
    base = default_config()
    if not path.exists():
        return base
    with path.open("rb") as handle:
        loaded = tomllib.load(handle)
    merged = {**base, **loaded}
    worker = {**base["worker"], **(loaded.get("worker") or {})}
    merged["worker"] = worker
    return merged


def _default_save_path() -> Path:
    if local_config_path().is_file():
        return local_config_path()
    if global_config_path().is_file():
        return global_config_path()
    return local_config_path()


def save_config(data: dict[str, Any], *, path: Path | None = None) -> Path:
    """Write configuration to disk with restrictive permissions.

    :param data: Configuration mapping to persist.
    :param path: Optional explicit path; defaults to project-local or global file.
    :returns: Path written.
    """
    target = path or _default_save_path()
    directory = target.parent
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    with target.open("wb") as handle:
        tomli_w.dump(data, handle)
    target.chmod(0o600)
    return target
