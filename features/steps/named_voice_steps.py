"""Behave steps for named voices that must fail loudly when missing."""

from __future__ import annotations

import io
import os
import sys
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock

import httpx
from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))

CLONING_BACKENDS = (
    "auritus.tts.fish:FishBackend",
    "auritus.tts.chatterbox:ChatterboxBackend",
    "auritus.tts.f5:F5Backend",
)


def _cloning_backend_classes():
    import importlib

    classes = []
    for spec in CLONING_BACKENDS:
        module, _, name = spec.partition(":")
        classes.append(getattr(importlib.import_module(module), name))
    return classes


def _short_wav() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\0\0" * 240)
    return buffer.getvalue()


def _unset_voices_env(context) -> None:
    previous = os.environ.pop("AURITUS_VOICES", None)
    if previous is not None:
        context.add_cleanup(os.environ.__setitem__, "AURITUS_VOICES", previous)


@given("the cloning speech models are stubbed")
def step_stub_cloning_models(context) -> None:
    context.spoken_references = []

    def stub(self, text, meta, reference):
        context.spoken_references.append(reference)
        return _short_wav()

    for cls in _cloning_backend_classes():
        for method in ("_generate_mlx", "_generate_torch"):
            original = cls.__dict__[method]
            setattr(cls, method, stub)
            context.add_cleanup(setattr, cls, method, original)


@when('I try to synthesize "{text}" with voice "{voice}" from that folder')
def step_try_synthesize_from_folder(context, text: str, voice: str) -> None:
    from auritus.speech import Voice, synthesize

    context.speech = None
    try:
        context.speech = synthesize(
            text, Voice.parse(voice), voices_dir=context.voices_dir
        )
        context.error = None
    except Exception as exc:  # noqa: BLE001 - the scenario inspects the error
        context.error = exc


def _assert_voice_not_found(context, voice: str):
    from auritus.tts.voices import VoiceNotFound

    assert isinstance(context.error, VoiceNotFound), repr(context.error)
    assert context.error.voice_id == voice, context.error.voice_id
    assert repr(voice) in str(context.error), str(context.error)
    return context.error


@then('a VoiceNotFound error names "{voice}" and says no voices folder is configured')
def step_voice_not_found_no_folder(context, voice: str) -> None:
    error = _assert_voice_not_found(context, voice)
    assert error.directory is None, error.directory
    assert "AURITUS_VOICES" in str(error), str(error)


@then('a VoiceNotFound error names "{voice}" and that voices folder')
def step_voice_not_found_in_folder(context, voice: str) -> None:
    error = _assert_voice_not_found(context, voice)
    assert error.directory == Path(context.voices_dir), error.directory
    assert str(context.voices_dir) in str(error), str(error)


@then("no speech was returned")
def step_no_speech(context) -> None:
    assert context.speech is None, "speech was returned for a missing voice"


@then('the stubbed model spoke with that folder\'s "{name}"')
def step_spoke_with_reference(context, name: str) -> None:
    assert context.error is None, repr(context.error)
    expected = (Path(context.voices_dir) / name).resolve()
    assert context.spoken_references == [expected], context.spoken_references


@then("the stubbed model spoke with the stock voice")
def step_spoke_with_stock_voice(context) -> None:
    assert context.error is None, repr(context.error)
    assert context.spoken_references == [None], context.spoken_references


@given('the Auritus API has a "{backend}" job for voice "{voice}"')
def step_api_has_job(context, backend: str, voice: str) -> None:
    context.worker_requests = []
    job = {
        "text": "Some article text.",
        "voice_id": voice,
        "tts_backend": backend,
        "name": "",
        "byline": "",
    }

    def respond(method: str, url: str, **kwargs) -> httpx.Response:
        context.worker_requests.append((method, url, kwargs.get("json")))
        request = httpx.Request(method, url)
        if url.endswith("/redeem"):
            body = {"access_token": "worker-bearer", "job": job}
            return httpx.Response(200, json=body, request=request)
        if url.endswith("/presign-upload"):
            body = {
                "upload_url": "https://uploads.auritus.test/audio.wav",
                "audio_key": "audio/job.wav",
            }
            return httpx.Response(200, json=body, request=request)
        return httpx.Response(200, json={}, request=request)

    context.worker_responder = respond


@given("the Batch image has no reference voices")
def step_batch_image_no_voices(context) -> None:
    _unset_voices_env(context)


def _batch_requests_to(context, suffix: str) -> list:
    return [
        (method, body)
        for method, url, body in context.worker_requests
        if url.endswith(suffix)
    ]


@then('the Batch worker marks the job failed with a reason naming "{voice}"')
def step_batch_marks_failed(context, voice: str) -> None:
    failed = _batch_requests_to(context, "/failed")
    assert len(failed) == 1, context.worker_requests
    method, body = failed[0]
    assert method == "PUT", method
    assert repr(voice) in body["reason"], body["reason"]
    assert context.worker_exit_code == 1, context.worker_exit_code


@then("the Batch worker does not mark the job done")
def step_batch_not_done(context) -> None:
    assert not _batch_requests_to(context, "/done"), context.worker_requests


@then("the Batch worker marks the job done")
def step_batch_marks_done(context) -> None:
    assert _batch_requests_to(context, "/done"), context.worker_requests
    assert not _batch_requests_to(context, "/failed"), context.worker_requests
    assert context.worker_exit_code == 0, context.worker_exit_code


@given('a claimable "{backend}" job for voice "{voice}" with an empty voices folder')
def step_claimable_named_voice_job(context, backend: str, voice: str) -> None:
    from auritus.tts import get_backend

    _unset_voices_env(context)
    folder = tempfile.TemporaryDirectory()
    context.add_cleanup(folder.cleanup)
    context.worker_voices_dir = folder.name
    context.mock_client = MagicMock()
    context.mock_client.list_claimable.return_value = [
        {
            "content_hash": "worker-crash-hash-001",
            "text": "Some article text.",
            "tts_backend": backend,
            "voice_id": voice,
            "name": "",
            "byline": "",
        }
    ]
    context.mock_client.claim_job.return_value = {"status": "claimed"}
    context.mock_client.presign_upload.return_value = {
        "upload_url": "https://uploads.example.com/audio/worker-crash-hash-001.wav",
        "audio_key": "audio/worker-crash-hash-001.wav",
    }
    context.mock_backend = get_backend(backend)


@then('the failure reason names "{voice}"')
def step_failure_reason_names(context, voice: str) -> None:
    _, kwargs = context.mock_client.mark_failed.call_args
    assert repr(voice) in kwargs["reason"], kwargs["reason"]
