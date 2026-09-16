"""Tests for Auritus config helpers."""

from __future__ import annotations

from pathlib import Path

from auritus.config import default_config, load_config, save_config


def test_default_config_has_worker_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("auritus.config.config_dir", lambda: tmp_path)
    cfg = default_config()
    assert cfg["worker"]["claim_timeout"] == 900
    assert cfg["worker"]["tts_backend"] == "kokoro"


def test_save_and_load_roundtrip(tmp_path: Path, monkeypatch) -> None:
    # save_config() with no explicit path resolves via _default_save_path(),
    # which checks local_config_path() (Path.cwd() / ".auritus" / "config")
    # *before* falling back to the global path -- and falls back to the
    # *local* path, not the global one, when neither file exists yet.
    # Patching only config_dir() (the global directory) leaves local_config_path()
    # pointed at the real, unmocked cwd: every run of this test used to write
    # a real .auritus/config (with this test's own placeholder api_endpoint)
    # into whatever directory pytest happened to be invoked from, silently
    # shadowing the real global config for any auritus command run there
    # afterward. chdir into the sandbox so Path.cwd() -- and therefore
    # local_config_path() -- resolves inside tmp_path too.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("auritus.config.config_dir", lambda: tmp_path)
    cfg = default_config()
    cfg["api_endpoint"] = "https://example.execute-api.us-east-1.amazonaws.com"
    save_config(cfg)
    loaded = load_config()
    assert loaded["api_endpoint"].startswith("https://example")
    assert loaded["worker"]["poll_interval"] == 5
