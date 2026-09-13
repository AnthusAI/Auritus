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
    monkeypatch.setattr("auritus.config.config_dir", lambda: tmp_path)
    cfg = default_config()
    cfg["api_endpoint"] = "https://example.execute-api.us-east-1.amazonaws.com"
    save_config(cfg)
    loaded = load_config()
    assert loaded["api_endpoint"].startswith("https://example")
    assert loaded["worker"]["poll_interval"] == 5
