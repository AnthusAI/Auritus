"""Behave steps for the embeddable speech library (``auritus.speech``)."""

from __future__ import annotations

import io
import sys
import wave
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cli" / "src"))


def _synthesize(text: str, voice: str, speed: float = 1.0):
    from auritus.speech import SpeechOptions, Voice, synthesize

    return synthesize(text, Voice.parse(voice), SpeechOptions(speed=speed))


@when('I synthesize "{text}" with voice "{voice}" at speed {speed:f}')
def step_synthesize_speed(context, text: str, voice: str, speed: float) -> None:
    context.line_text, context.voice = text, voice
    try:
        context.speech = _synthesize(text, voice, speed)
        context.error = None
    except Exception as exc:  # noqa: BLE001 - the scenario inspects the error
        context.speech, context.error = None, exc


@when('I synthesize "{text}" with voice "{voice}"')
def step_synthesize(context, text: str, voice: str) -> None:
    context.speech = _synthesize(text, voice)


@then("I receive mono WAV audio at {rate:d} Hz")
def step_wav(context, rate: int) -> None:
    with wave.open(io.BytesIO(context.speech.wav)) as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == rate
        context.wav_seconds = wav.getnframes() / wav.getframerate()
    assert context.speech.sample_rate == rate


@then("the reported duration matches the audio")
def step_duration(context) -> None:
    assert abs(context.speech.duration - context.wav_seconds) < 1e-6


@then("the result lists {count:d} timed segments")
def step_segment_count(context, count: int) -> None:
    assert len(context.speech.segments) == count, context.speech.segments


@then('segment 1 is "{first}" and ends before segment 2 "{second}" starts')
def step_segment_order(context, first: str, second: str) -> None:
    one, two = context.speech.segments[:2]
    assert (one.text, two.text) == (first, second)
    assert 0 == one.start < one.end < two.start < two.end
    assert abs(two.end - context.speech.duration) < 1e-6


@then(
    'the provenance records engine "{engine}", backend "{backend}", '
    'model "{model}" and voice "{voice}"'
)
def step_provenance(context, engine, backend, model, voice) -> None:
    from auritus import __version__

    prov = context.speech.provenance
    assert prov["engine"] == engine
    assert prov["version"] == __version__
    assert prov["backend"] == backend
    assert prov["model"] == model
    assert prov["voice"] == voice


@when('I parse the voice spec "{spec}"')
def step_parse_voice(context, spec: str) -> None:
    from auritus.speech import Voice

    context.parsed_voice = Voice.parse(spec)


@then('the voice backend is "{backend}" and its id is "{voice_id}"')
def step_parsed_voice(context, backend: str, voice_id: str) -> None:
    assert context.parsed_voice.backend == backend
    assert context.parsed_voice.id == voice_id


@then("the audio is shorter than the same line at speed {speed:f}")
def step_shorter(context, speed: float) -> None:
    slower = _synthesize(context.line_text, context.voice, speed)
    assert context.speech.duration < slower.duration
    assert context.speech.request_key != slower.request_key


@then('synthesis fails because "{backend}" does not support speed')
def step_speed_refused(context, backend: str) -> None:
    from auritus.speech import UnsupportedOption

    assert isinstance(context.error, UnsupportedOption), context.error
    assert backend in str(context.error) and "speed" in str(context.error)


@given('the request "{text}" with voice "{voice}"')
def step_request(context, text: str, voice: str) -> None:
    context.line_text, context.voice = text, voice


def _key(context, text=None, voice=None, speed=1.0, seed=None) -> str:
    from auritus.speech import SpeechOptions, Voice, request_key

    return request_key(
        text if text is not None else context.line_text,
        Voice.parse(voice or context.voice),
        SpeechOptions(speed=speed, seed=seed),
    )


@then("its request key is the same when computed twice")
def step_key_stable(context) -> None:
    context.key = _key(context)
    assert context.key == _key(context)
    assert len(context.key) == 64


@then('its request key changes when the text is "{text}"')
def step_key_text(context, text: str) -> None:
    assert _key(context, text=text) != context.key


@then('its request key changes when the voice is "{voice}"')
def step_key_voice(context, voice: str) -> None:
    assert _key(context, voice=voice) != context.key


@then("its request key changes when the speed is {speed:f}")
def step_key_speed(context, speed: float) -> None:
    assert _key(context, speed=speed) != context.key


@then("its request key changes when the seed is {seed:d}")
def step_key_seed(context, seed: int) -> None:
    assert _key(context, seed=seed) != context.key


@then("the synthesized result carries the same request key")
def step_key_on_result(context) -> None:
    assert _synthesize(context.line_text, context.voice).request_key == context.key
