"""Behave steps for pluggable TTS backend registry scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

from behave import then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "worker-image" / "src"))


@when("the TTS backend registry is loaded")
def step_load_registry(context) -> None:
    from tts import get_backend

    context.registered_backends = [
        get_backend(name).name
        for name in ("higgs", "qwen", "kokoro", "f5", "chatterbox")
    ]


@then('registered backends include "{name}"')
def step_backend_registered(context, name: str) -> None:
    assert name in context.registered_backends


@when("the TTS backend is resolved from the registry")
def step_resolve_backend(context) -> None:
    from tts import get_backend

    context.resolved_backend = get_backend(context.tts_backend)


@then('the resolved backend name is "{name}"')
def step_resolved_backend_name(context, name: str) -> None:
    assert context.resolved_backend.name == name
