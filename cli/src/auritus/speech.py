"""Typed, offline speech synthesis for host applications.

This is the library surface other programs embed (Apricity is the first)::

    from auritus.speech import Voice, synthesize

    speech = synthesize("Welcome to the show.", Voice.parse("kokoro:af_heart"))
    speech.wav            # mono 16-bit WAV bytes
    speech.segments       # one timed Segment per [[auritus:break]] block
    speech.request_key    # stable cache key for this exact request

It needs no login, config file or AWS: only the chosen backend's own
dependencies.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
import wave
from dataclasses import asdict, dataclass, field
from typing import Any

from auritus import __version__
from auritus.tts import get_backend
from auritus.tts.base import BackendUnavailable, TTSBackend
from auritus.tts.breaks import DEFAULT_BREAK_SILENCE_SECONDS, parse_voiced_segments

__all__ = [
    "BackendUnavailable",
    "Segment",
    "Speech",
    "SpeechOptions",
    "UnsupportedOption",
    "Voice",
    "request_key",
    "synthesize",
]

DEFAULT_VOICE_ID = "default"


class UnsupportedOption(ValueError):
    """A request asked a backend for something it cannot do."""


@dataclass(frozen=True)
class Voice:
    """A backend plus one of its voices, written ``backend:id``.

    :param backend: Backend name, as accepted by :func:`auritus.tts.get_backend`.
    :param id: Voice id within that backend; ``default`` lets it choose.
    """

    backend: str
    id: str = DEFAULT_VOICE_ID

    @classmethod
    def parse(cls, spec: str) -> Voice:
        """Parse ``"kokoro:af_heart"`` (or just ``"kokoro"``).

        :param spec: Voice spec string.
        :returns: The parsed voice.
        :raises ValueError: If the backend part is empty.
        """
        backend, _, voice_id = spec.strip().partition(":")
        if not backend.strip():
            raise ValueError(
                f"Voice spec needs a backend, e.g. 'kokoro:af_heart': {spec!r}"
            )
        return cls(backend.strip().lower(), voice_id.strip() or DEFAULT_VOICE_ID)

    def __str__(self) -> str:
        return f"{self.backend}:{self.id}"


@dataclass(frozen=True)
class SpeechOptions:
    """How to speak, beyond which voice.

    :param speed: Speaking-rate multiplier; only backends that support it
        accept anything but ``1.0``.
    :param seed: Seed for Python, NumPy, PyTorch and MLX random generators,
        for backends that sample.
    """

    speed: float = 1.0
    seed: int | None = None


@dataclass(frozen=True)
class Segment:
    """One ``[[auritus:break]]``-delimited block and where it sits in the audio.

    :param text: The block's text, markers removed.
    :param voice: Voice id the block was spoken with.
    :param start: Start time in seconds.
    :param end: End time in seconds.
    """

    text: str
    voice: str
    start: float
    end: float


@dataclass(frozen=True)
class Speech:
    """Synthesized speech and everything known about how it was made.

    :param wav: Mono 16-bit WAV bytes.
    :param sample_rate: Sample rate in Hz.
    :param duration: Length in seconds.
    :param segments: Timed blocks, in order.
    :param provenance: Engine, version, backend, model, voice and options.
    :param request_key: :func:`request_key` of the request that made it.
    """

    wav: bytes = field(repr=False)
    sample_rate: int
    duration: float
    segments: tuple[Segment, ...]
    provenance: dict[str, Any]
    request_key: str


def _options_dict(options: SpeechOptions) -> dict[str, Any]:
    return asdict(options)


def _request_key(text: str, voice: Voice, options: SpeechOptions, model: str) -> str:
    canonical = json.dumps(
        {
            "engine": "auritus",
            "backend": voice.backend,
            "model": model,
            "voice": voice.id,
            "text": text,
            "options": _options_dict(options),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def request_key(text: str, voice: Voice, options: SpeechOptions | None = None) -> str:
    """Stable SHA-256 identifying exactly what :func:`synthesize` would make.

    It covers the text, backend, model, voice and options, and not the Auritus
    version, so upgrades keep caches warm unless the model changes. It never
    loads a model.

    :param text: Text to speak.
    :param voice: Voice to speak it with.
    :param options: Speaking options (defaults if omitted).
    :returns: 64-character hex digest.
    """
    backend = get_backend(voice.backend)
    return _request_key(text, voice, options or SpeechOptions(), backend.model_id())


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
    except ImportError:
        pass
    try:
        import mlx.core as mx

        mx.random.seed(seed)
    except ImportError:
        pass


def _read_wav(data: bytes) -> tuple[Any, bytes]:
    with wave.open(io.BytesIO(data)) as wav:
        return wav.getparams(), wav.readframes(wav.getnframes())


def synthesize(text: str, voice: Voice, options: SpeechOptions | None = None) -> Speech:
    """Speak ``text`` offline and return audio with timing and provenance.

    Each ``[[auritus:break]]`` block is synthesized separately and joined with
    the standard break silence, which is what makes segment timings exact.
    Inline ``[[auritus:voice:<id>]]`` markers switch voice between blocks.

    :param text: Text to speak, optionally with Auritus markers.
    :param voice: Backend and voice.
    :param options: Speaking options (defaults if omitted).
    :returns: The synthesized speech.
    :raises ValueError: If ``text`` has nothing to speak or the backend is
        unknown.
    :raises UnsupportedOption: If the backend cannot honour ``options``.
    :raises BackendUnavailable: If the backend's libraries are missing or it
        cannot run on this machine.
    """
    options = options or SpeechOptions()
    backend: TTSBackend = get_backend(voice.backend)
    if options.speed != 1.0 and not backend.supports_speed:
        raise UnsupportedOption(
            f"The {backend.name!r} backend does not support speed; "
            f"got speed={options.speed}"
        )
    blocks = parse_voiced_segments(text, voice.id)
    if not blocks:
        raise ValueError("Nothing to speak: the text is empty after removing markers")
    if options.seed is not None:
        _seed_everything(options.seed)

    params = None
    frames: list[bytes] = []
    segments: list[Segment] = []
    cursor = 0
    for block_text, block_voice in blocks:
        meta: dict[str, Any] = {"voice_id": block_voice}
        if backend.supports_speed:
            meta["speed"] = options.speed
        try:
            audio = backend.generate(block_text, meta)
        except ImportError as exc:
            raise BackendUnavailable.from_import_error(backend.name, exc) from exc
        block_params, block_frames = _read_wav(audio)
        if block_params.nchannels != 1 or block_params.sampwidth != 2:
            raise ValueError(
                f"The {backend.name!r} backend returned "
                f"{block_params.nchannels}-channel {8 * block_params.sampwidth}-bit "
                "audio; expected mono 16-bit"
            )
        if params is None:
            params = block_params
            silence = b"\0\0" * int(params.framerate * DEFAULT_BREAK_SILENCE_SECONDS)
        elif block_params.framerate != params.framerate:
            raise ValueError(
                f"The {backend.name!r} backend changed sample rate mid-request"
            )
        if frames:
            frames.append(silence)
            cursor += len(silence) // 2
        start = cursor
        frames.append(block_frames)
        cursor += len(block_frames) // 2
        segments.append(
            Segment(
                block_text,
                block_voice,
                start / params.framerate,
                cursor / params.framerate,
            )
        )

    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(params.framerate)
        out.writeframes(b"".join(frames))

    model = backend.model_id()
    return Speech(
        wav=buf.getvalue(),
        sample_rate=params.framerate,
        duration=cursor / params.framerate,
        segments=tuple(segments),
        provenance={
            "engine": "auritus",
            "version": __version__,
            "backend": backend.name,
            "model": model,
            "voice": str(voice),
            "options": _options_dict(options),
        },
        request_key=_request_key(text, voice, options, model),
    )
