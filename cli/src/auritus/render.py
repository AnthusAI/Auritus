"""Batch render mode: speak one request and write the result for the host.

The worker image runs this (``AURITUS_MODE=render``) when a host's own cloud
deployment, the ``SpeechRenderer`` construct, submits a job. It never talks
to the Auritus API. The request comes from ``AURITUS_RENDER_REQUEST``, a JSON
object::

    {"text": "...", "voice": "kokoro:af_heart", "speed": 1.0, "seed": null,
     "output": "s3://bucket/prefix"}

``output`` is an ``s3://`` URI or a local folder. On success the renderer
writes ``speech.wav`` and ``speech.json`` (sample rate, duration, segments,
provenance, request key, and the request itself) and exits 0. On any failure
it writes ``error.json`` (``error``, ``message`` and, for a missing library,
``missing_module``) and exits 1. So the host always finds one or the other.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from auritus.speech import SpeechOptions, Voice, synthesize
from auritus.tts.base import BackendUnavailable

__all__ = ["MAX_TEXT_CHARACTERS", "RenderError", "main"]

#: Longest text one render accepts; longer requests should be split by the host.
MAX_TEXT_CHARACTERS = 5000


class RenderError(Exception):
    """A request the renderer refuses, with a machine-readable kind."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


class _Output:
    """Where results go: an ``s3://bucket/prefix`` or a local folder."""

    def __init__(self, uri: str) -> None:
        self.uri = uri
        if uri.startswith("s3://"):
            bucket, _, prefix = uri[len("s3://") :].partition("/")
            self.bucket, self.prefix = bucket, prefix.strip("/")
            self.folder = None
        else:
            self.bucket = self.prefix = None
            self.folder = Path(uri)

    def write(self, name: str, data: bytes, content_type: str) -> None:
        if self.folder is not None:
            self.folder.mkdir(parents=True, exist_ok=True)
            (self.folder / name).write_bytes(data)
            return
        import boto3

        key = f"{self.prefix}/{name}" if self.prefix else name
        boto3.client("s3").put_object(
            Bucket=self.bucket, Key=key, Body=data, ContentType=content_type
        )


def _parse_request(env: Mapping[str, str]) -> dict[str, Any]:
    raw = env.get("AURITUS_RENDER_REQUEST", "")
    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RenderError("InvalidRequest", f"request is not JSON: {exc}") from exc
    if not isinstance(request, dict):
        raise RenderError("InvalidRequest", "request must be a JSON object")
    return request


def _validate(request: dict[str, Any], env: Mapping[str, str]) -> tuple:
    text = request.get("text")
    if not isinstance(text, str) or not text.strip():
        raise RenderError("InvalidRequest", "request needs non-empty 'text'")
    if len(text) > MAX_TEXT_CHARACTERS:
        raise RenderError(
            "InvalidRequest",
            f"text is {len(text)} characters; the limit is {MAX_TEXT_CHARACTERS}",
        )
    try:
        voice = Voice.parse(str(request.get("voice") or "kokoro"))
        options = SpeechOptions(
            speed=float(request.get("speed") or 1.0),
            seed=None if request.get("seed") is None else int(request["seed"]),
        )
    except (TypeError, ValueError) as exc:
        raise RenderError("InvalidRequest", str(exc)) from exc
    allowed = [
        b.strip().lower()
        for b in env.get("AURITUS_ALLOWED_BACKENDS", "").split(",")
        if b.strip()
    ]
    if allowed and voice.backend not in allowed:
        raise RenderError(
            "BackendNotAllowed",
            f"backend {voice.backend!r} is not enabled here; allowed: {allowed}",
        )
    return text, voice, options


def _error_body(exc: BaseException) -> dict[str, Any]:
    body: dict[str, Any] = {"error": type(exc).__name__, "message": str(exc)}
    if isinstance(exc, RenderError):
        body["error"] = exc.kind
    if isinstance(exc, BackendUnavailable):
        body["backend"] = exc.backend
        body["missing_module"] = exc.missing_module
    return body


def main(env: Mapping[str, str] | None = None) -> int:
    """Render the request in ``env`` and write the result.

    :param env: Environment to read (default: ``os.environ``).
    :returns: 0 when speech was written, 1 when ``error.json`` was.
    """
    env = os.environ if env is None else env
    try:
        request = _parse_request(env)
    except RenderError as exc:
        print(f"[render] {exc}", file=sys.stderr, flush=True)
        return 1
    output = request.get("output")
    if not isinstance(output, str) or not output:
        print("[render] request needs 'output'", file=sys.stderr, flush=True)
        return 1
    out = _Output(output)
    try:
        text, voice, options = _validate(request, env)
        print(f"[render] {voice} {len(text)} chars -> {out.uri}", flush=True)
        speech = synthesize(
            text, voice, options, voices_dir=env.get("AURITUS_VOICES") or None
        )
        out.write("speech.wav", speech.wav, "audio/wav")
        meta = {
            "sample_rate": speech.sample_rate,
            "duration": speech.duration,
            "segments": [asdict(s) for s in speech.segments],
            "provenance": speech.provenance,
            "request_key": speech.request_key,
            "request": {k: request.get(k) for k in ("text", "voice", "speed", "seed")},
        }
        out.write(
            "speech.json", json.dumps(meta, indent=1).encode(), "application/json"
        )
        print(f"[render] done: {speech.duration:.2f}s", flush=True)
        return 0
    except Exception as exc:  # noqa: BLE001 - every failure must reach error.json
        traceback.print_exc()
        out.write(
            "error.json",
            json.dumps(_error_body(exc), indent=1).encode(),
            "application/json",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
