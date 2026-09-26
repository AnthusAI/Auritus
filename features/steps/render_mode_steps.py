"""Behave steps for the Batch render mode (``auritus.render``)."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import wave
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))


def _output_dir(context) -> Path:
    if not hasattr(context, "render_out"):
        tmp = tempfile.TemporaryDirectory()
        context.add_cleanup(tmp.cleanup)
        context.render_out = Path(tmp.name)
        context.render_env = {}
    return context.render_out


def _request(context, **fields) -> None:
    out = _output_dir(context)
    context.render_request = {"output": str(out), **fields}
    context.render_env["AURITUS_RENDER_REQUEST"] = json.dumps(context.render_request)


@given('a render request for "{text}" with voice "{voice}"')
def step_render_request(context, text: str, voice: str) -> None:
    _request(context, text=text, voice=voice)


@given("a render request with no text")
def step_render_request_no_text(context) -> None:
    _request(context, text="  ", voice="fake:plain")


@given('the deployment allows only the "{backend}" backend')
def step_allowed_backends(context, backend: str) -> None:
    _output_dir(context)
    context.render_env["AURITUS_ALLOWED_BACKENDS"] = backend


@when("the renderer runs")
def step_renderer_runs(context) -> None:
    from auritus.render import main

    context.render_exit = main(context.render_env)


@then("it exits successfully")
def step_exit_ok(context) -> None:
    assert context.render_exit == 0, context.render_exit


@then("it exits with a failure")
def step_exit_failed(context) -> None:
    assert context.render_exit != 0


@then('the output has "{name}" as mono WAV audio')
def step_output_wav(context, name: str) -> None:
    data = (context.render_out / name).read_bytes()
    with wave.open(io.BytesIO(data)) as wav:
        assert wav.getnchannels() == 1
        context.render_wav_seconds = wav.getnframes() / wav.getframerate()


def _json(context, name: str) -> dict:
    return json.loads((context.render_out / name).read_text())


@then(
    '"{name}" records {count:d} timed segments, the sample rate, duration, '
    "provenance and request key"
)
def step_speech_json(context, name: str, count: int) -> None:
    meta = _json(context, name)
    assert len(meta["segments"]) == count, meta["segments"]
    assert all({"text", "start", "end"} <= set(s) for s in meta["segments"])
    assert meta["sample_rate"] == 24000
    assert abs(meta["duration"] - context.render_wav_seconds) < 1e-6
    assert meta["provenance"]["engine"] == "auritus"
    assert meta["provenance"]["backend"] == "fake"
    assert len(meta["request_key"]) == 64


@then('"{name}" echoes the request')
def step_echo_request(context, name: str) -> None:
    echoed = _json(context, name)["request"]
    assert echoed["text"] == context.render_request["text"]
    assert echoed["voice"] == context.render_request["voice"]


@then('"{name}" says "{kind}" and names the missing module')
def step_error_missing_module(context, name: str, kind: str) -> None:
    error = _json(context, name)
    assert error["error"] == kind, error
    assert error["missing_module"], error


@then('"{name}" says "{kind}"')
def step_error_kind(context, name: str, kind: str) -> None:
    error = _json(context, name)
    assert error["error"] == kind, error
    assert error["message"], error


@then('the output has no "{name}"')
def step_no_output(context, name: str) -> None:
    assert not (context.render_out / name).exists()
