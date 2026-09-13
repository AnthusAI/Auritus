"""AWS Batch GPU worker entrypoint."""

from __future__ import annotations

import os
import sys
import traceback
from typing import Any

import httpx
from tts.registry import get_backend


def _require_env(primary: str, *aliases: str) -> str:
    for key in (primary, *aliases):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    names = ", ".join((primary, *aliases))
    raise KeyError(f"Missing required environment variable (one of): {names}")


def _resolve_voice_id(raw: str | None) -> str:
    if not raw or raw == "default":
        return "af_heart"
    return raw


def _auth_headers(bearer: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _install_backend(name: str) -> None:
    """Install TTS packages at runtime if not already present.

    :param name: Backend name (kokoro, qwen, etc.).
    """
    import importlib
    import sys

    try:
        importlib.import_module(f"tts.{name}")
    except ImportError:
        print(f"Installing TTS backend: {name}...")
        import subprocess

        packages = {
            "kokoro": ["kokoro>=0.9.0", "torch", "soundfile"],
            "qwen": ["qwen-tts", "torch", "soundfile"],
            "higgs": ["torch", "soundfile"],
            "fish": ["fish-speech", "torch", "soundfile"],
            "coqui": ["TTS", "torch", "soundfile"],
            "bark": ["transformers", "torch", "soundfile"],
        }
        deps = packages.get(name, packages.get(name, ["torch", "soundfile"]))
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *deps],
            check=True,
        )


def redeem_job_token(
    api_url: str, job_hash: str, job_token: str
) -> tuple[str, dict[str, Any]]:
    """Exchange the single-job token for a worker-scoped bearer and optional job payload.

    :returns: Tuple of (bearer token, job fields such as text and voice_id).
    """
    response = httpx.post(
        f"{api_url}/jobs/{job_hash}/redeem",
        headers=_auth_headers(job_token),
        json={"job_token": job_token},
        timeout=30.0,
    )
    if response.status_code == 404:
        return job_token, {}
    response.raise_for_status()
    body = response.json()
    bearer = str(body.get("access_token") or body.get("bearer") or job_token)
    job = body.get("job") if isinstance(body.get("job"), dict) else body
    return bearer, job


def mark_failed(
    api_url: str,
    job_hash: str,
    headers: dict[str, str],
    *,
    owner: str,
    reason: str,
) -> None:
    """Best-effort failure notification for operators and Step Functions."""
    try:
        httpx.put(
            f"{api_url}/jobs/{job_hash}/failed",
            headers=headers,
            json={"owner": owner, "reason": reason},
            timeout=30.0,
        )
    except httpx.HTTPError:
        pass


def main() -> int:
    """Redeem token, claim job, generate TTS, upload, and mark done or failed."""
    api_url = _require_env("API_URL", "AURITUS_API_ENDPOINT").rstrip("/")
    job_hash = _require_env("JOB_HASH", "AURITUS_CONTENT_HASH")
    job_token = _require_env("JOB_TOKEN", "AURITUS_JOB_TOKEN")
    default_backend = os.environ.get("TTS_BACKEND") or os.environ.get(
        "AURITUS_TTS_BACKEND", "kokoro"
    )
    owner = f"batch:{os.environ.get('AWS_BATCH_JOB_ID', 'unknown')}"

    bearer, redeemed_job = redeem_job_token(api_url, job_hash, job_token)
    headers = _auth_headers(bearer)

    job_body: dict[str, Any] = dict(redeemed_job)
    if not job_body.get("text"):
        job_response = httpx.get(
            f"{api_url}/jobs/{job_hash}",
            headers=headers,
            timeout=30.0,
        )
        job_response.raise_for_status()
        job_body = job_response.json()

    claim = httpx.put(
        f"{api_url}/jobs/{job_hash}/claim",
        headers=headers,
        json={"claim_owner": owner},
        timeout=30.0,
    )
    if claim.status_code >= 400:
        print(f"claim failed: {claim.status_code} {claim.text}", file=sys.stderr)
        return 0

    try:
        backend_name = job_body.get("tts_backend") or default_backend
        _install_backend(backend_name)
        backend = get_backend(str(backend_name))
        audio = backend.generate(
            job_body.get("text") or "",
            {
                "voice_id": _resolve_voice_id(job_body.get("voice_id")),
                "name": job_body.get("name") or "",
                "byline": job_body.get("byline") or "",
            },
        )

        presign = httpx.post(
            f"{api_url}/jobs/{job_hash}/presign-upload",
            headers=headers,
            json={},
            timeout=30.0,
        )
        presign.raise_for_status()
        upload = presign.json()
        put = httpx.put(
            upload["upload_url"],
            content=audio,
            timeout=300.0,
        )
        put.raise_for_status()

        done = httpx.put(
            f"{api_url}/jobs/{job_hash}/done",
            headers=headers,
            json={"audio_key": upload["audio_key"], "owner": owner},
            timeout=30.0,
        )
        done.raise_for_status()
        print(f"done {job_hash}")
        return 0
    except (httpx.HTTPError, OSError, ValueError, KeyError) as exc:
        reason = f"{type(exc).__name__}: {exc}"
        print(reason, file=sys.stderr)
        traceback.print_exc()
        mark_failed(api_url, job_hash, headers, owner=owner, reason=reason)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
