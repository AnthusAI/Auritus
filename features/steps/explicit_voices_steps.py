"""Behave steps for explicit reference-voice folders."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))


def _tmpdir(context) -> Path:
    tmp = tempfile.TemporaryDirectory()
    context.add_cleanup(tmp.cleanup)
    return Path(tmp.name)


def _touch_voice(folder: Path, *names: str) -> None:
    for name in names:
        (folder / name).write_text(
            "reference transcript" if name.endswith(".txt") else "RIFF"
        )


def _unset_voices_env(context) -> None:
    previous = os.environ.pop("AURITUS_VOICES", None)
    if previous is not None:
        context.add_cleanup(os.environ.__setitem__, "AURITUS_VOICES", previous)


@given('a voices folder containing "{audio}" and "{text}"')
def step_voices_folder(context, audio: str, text: str) -> None:
    _unset_voices_env(context)
    context.voices_dir = _tmpdir(context)
    _touch_voice(context.voices_dir, audio, text)


@given("no voices folder is configured")
def step_no_voices_folder(context) -> None:
    _unset_voices_env(context)
    context.voices_dir = None


@given('the current directory contains "{name}"')
def step_cwd_contains(context, name: str) -> None:
    cwd = _tmpdir(context)
    _touch_voice(cwd, name)
    (cwd / "voices").mkdir()
    _touch_voice(cwd / "voices", name)
    previous = os.getcwd()
    os.chdir(cwd)
    context.add_cleanup(os.chdir, previous)


@given('AURITUS_VOICES points at a folder containing "{audio}" and "{text}"')
def step_env_folder(context, audio: str, text: str) -> None:
    _unset_voices_env(context)
    folder = _tmpdir(context)
    _touch_voice(folder, audio, text)
    os.environ["AURITUS_VOICES"] = str(folder)
    context.add_cleanup(os.environ.pop, "AURITUS_VOICES", None)
    context.env_voices_dir = folder
    context.voices_dir = None


@when("I list reference voices from that folder")
def step_list_voices(context) -> None:
    from auritus.tts.voices import list_voices

    context.listed = list_voices(context.voices_dir)


@then('the listed voices are exactly "{names}"')
def step_listed(context, names: str) -> None:
    assert context.listed == names.split(","), context.listed


@when('I resolve reference audio for "{voice_id}" from that folder')
def step_resolve_from_folder(context, voice_id: str) -> None:
    from auritus.tts.voices import resolve_reference_audio

    context.reference = resolve_reference_audio(voice_id, context.voices_dir)


@when('I resolve reference audio for "{voice_id}"')
def step_resolve(context, voice_id: str) -> None:
    from auritus.tts.voices import resolve_reference_audio, resolve_reference_text

    context.reference = resolve_reference_audio(voice_id, context.voices_dir)
    context.transcript = resolve_reference_text(voice_id, context.voices_dir)


@then("no reference audio is found")
def step_none_found(context) -> None:
    assert context.reference is None, context.reference


@then('the reference is that folder\'s "{name}"')
def step_reference_is(context, name: str) -> None:
    assert context.reference == (context.env_voices_dir / name).resolve()


@then('the reference transcript is read from that folder\'s "{name}"')
def step_transcript_is(context, name: str) -> None:
    expected = (context.env_voices_dir / name).read_text().strip()
    assert context.transcript == expected


@when('I synthesize "{text}" with voice "{voice}" from that folder')
def step_synthesize_from_folder(context, text: str, voice: str) -> None:
    from auritus.speech import Voice, synthesize
    from auritus.tts.fake import FakeBackend

    seen: list = []
    original = FakeBackend.generate

    def spy(self, block_text, meta):
        seen.append(meta.get("voices_dir"))
        return original(self, block_text, meta)

    FakeBackend.generate = spy
    context.add_cleanup(setattr, FakeBackend, "generate", original)
    synthesize(text, Voice.parse(voice), voices_dir=context.voices_dir)
    context.seen_voices_dirs = seen


@then("the backend was given that voices folder")
def step_backend_given_folder(context) -> None:
    assert context.seen_voices_dirs == [context.voices_dir], context.seen_voices_dirs


@given("worker config without a voices_dir")
def step_worker_config(context) -> None:
    context.worker_cfg = {"tts_backend": "kokoro"}


@when('the worker\'s voices folder is resolved in "{cwd}"')
def step_worker_voices(context, cwd: str) -> None:
    from auritus.worker.daemon import worker_voices_dir

    context.worker_voices = worker_voices_dir(context.worker_cfg, cwd=Path(cwd))


@then('the worker voices folder is "{path}"')
def step_worker_voices_is(context, path: str) -> None:
    assert context.worker_voices == Path(path), context.worker_voices
