"""Behave steps for backends that must fail loudly instead of faking audio."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))

#: Top-level packages that hold speech models; hiding them simulates a
#: machine where no backend's libraries are installed.
MODEL_PACKAGES = (
    "boson_multimodal",
    "chatterbox",
    "f5_tts",
    "f5_tts_mlx",
    "fish_speech",
    "kokoro",
    "mlx",
    "mlx_audio",
    "qwen_tts",
    "torch",
    "torchaudio",
    "transformers",
)

CLI_BACKENDS = {
    "chatterbox": "auritus.tts.chatterbox:ChatterboxBackend",
    "f5": "auritus.tts.f5:F5Backend",
    "fish": "auritus.tts.fish:FishBackend",
    "higgs": "auritus.tts.higgs:HiggsBackend",
    "kokoro": "auritus.tts.kokoro:KokoroBackend",
    "qwen": "auritus.tts.qwen:QwenBackend",
}


def _backend_class(spec: str):
    module, _, name = spec.partition(":")
    return getattr(importlib.import_module(module), name)


def _hide_model_packages(context) -> None:
    """Make every import of a model package raise ImportError, until cleanup."""
    saved = {
        key: sys.modules[key]
        for key in list(sys.modules)
        if key.split(".")[0] in MODEL_PACKAGES
    }
    for key in [*saved, *MODEL_PACKAGES]:
        sys.modules[key] = None

    def restore() -> None:
        for key in MODEL_PACKAGES:
            sys.modules.pop(key, None)
        for key in saved:
            sys.modules.pop(key, None)
        sys.modules.update(saved)

    context.add_cleanup(restore)


def _force_mlx(context, classes, value: bool) -> None:
    """Pin each backend class's cached platform check, until cleanup."""
    for cls in classes:
        previous = cls._is_mlx
        cls._is_mlx = value
        context.add_cleanup(setattr, cls, "_is_mlx", previous)


@given("the speech model libraries are not installed")
def step_no_model_libraries(context) -> None:
    # Unless a step already chose the platform, pin the Apple Silicon path so
    # the scenario means the same on CI (Linux) as on a Mac.
    if not getattr(context, "platform_pinned", False):
        _force_mlx(context, [_backend_class(s) for s in CLI_BACKENDS.values()], True)
    _hide_model_packages(context)


@given("this machine is not Apple Silicon")
def step_not_apple_silicon(context) -> None:
    _force_mlx(context, [_backend_class(s) for s in CLI_BACKENDS.values()], False)
    context.platform_pinned = True


@when('I try to synthesize "{text}" with voice "{voice}"')
def step_try_synthesize(context, text: str, voice: str) -> None:
    from auritus.speech import Voice, synthesize

    context.speech = None
    try:
        context.speech = synthesize(text, Voice.parse(voice))
        context.error = None
    except Exception as exc:  # noqa: BLE001 - the scenario inspects the error
        context.error = exc


def _assert_unavailable(context, backend: str):
    from auritus import BackendUnavailable

    assert context.speech is None, "a stand-in result was returned"
    assert isinstance(context.error, BackendUnavailable), repr(context.error)
    assert context.error.backend == backend, context.error.backend
    return context.error


@then('a BackendUnavailable error names "{backend}" and a missing module')
def step_unavailable_missing_module(context, backend: str) -> None:
    error = _assert_unavailable(context, backend)
    assert error.missing_module, str(error)
    assert error.missing_module.split(".")[0] in MODEL_PACKAGES, str(error)
    assert error.missing_module in str(error)
