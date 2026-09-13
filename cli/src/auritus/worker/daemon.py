"""Local worker daemon that claims jobs and runs TTS on local GPU hardware."""

from __future__ import annotations

import socket
import threading
import time
import uuid

import httpx
import typer

from auritus.api import AuritusApiError, AuritusClient
from auritus.config import load_config
from auritus.tts import get_backend


def _heartbeat_loop(
    client: AuritusClient,
    content_hash: str,
    owner: str,
    stop: threading.Event,
    interval: int,
) -> None:
    while not stop.wait(interval):
        try:
            client.renew_claim(content_hash, owner)
        except AuritusApiError:
            pass


def run_worker(*, once: bool = False) -> None:
    """Poll claimable jobs and process them locally.

    :param once: If True, exit after processing zero or one job.
    """
    cfg = load_config()
    worker_cfg = cfg["worker"]
    poll_interval = int(worker_cfg["poll_interval"])
    claim_timeout = int(worker_cfg["claim_timeout"])
    tts_backend_name = str(worker_cfg["tts_backend"])
    heartbeat_interval = max(5, min(poll_interval, claim_timeout // 3))
    owner = f"local:{socket.gethostname()}:{uuid.uuid4().hex[:8]}"
    typer.echo(
        f"Worker starting as {owner} backend={tts_backend_name} "
        f"poll={poll_interval}s claim_timeout={claim_timeout}s"
    )

    try:
        client = AuritusClient()
    except AuritusApiError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise SystemExit(1) from exc

    backend = get_backend(tts_backend_name)

    while True:
        try:
            jobs = client.list_claimable()
            typer.echo(f"Found {len(jobs)} claimable jobs")
        except AuritusApiError as exc:
            typer.secho(
                f"list_claimable failed: {exc}",
                fg=typer.colors.YELLOW,
                err=True,
            )
            if once is True:
                return
            time.sleep(poll_interval)
            continue

        processed = False
        for job in jobs:
            content_hash = job.get("content_hash") or job.get("pk")
            if not content_hash:
                continue
            try:
                claim = client.claim_job(content_hash, owner)
            except AuritusApiError:
                typer.echo(f"Claim failed for {content_hash[:16]}", err=True)
                continue
            if (
                claim.get("status") not in {"claimed", "ok"}
                and claim.get("claim_owner") != owner
            ):
                continue
            typer.echo(f"Claimed {content_hash[:16]}")
            text = job.get("text") or ""
            job_backend = job.get("tts_backend") or tts_backend_name
            meta = {
                "voice_id": job.get("voice_id") or "default",
                "name": job.get("name") or "",
                "byline": job.get("byline") or "",
            }
            typer.echo(
                f"Generating audio for {content_hash[:16]} backend={job_backend}"
            )
            backend = get_backend(job_backend)
            stop = threading.Event()
            heartbeat = threading.Thread(
                target=_heartbeat_loop,
                args=(client, content_hash, owner, stop, heartbeat_interval),
                daemon=True,
            )
            heartbeat.start()
            try:
                audio_bytes = backend.generate(text, meta)
            finally:
                stop.set()
                heartbeat.join(timeout=1.0)

            upload = client.presign_upload(content_hash)
            upload_url = upload["upload_url"]
            audio_key = upload["audio_key"]
            put = httpx.put(
                upload_url,
                content=audio_bytes,
                timeout=120.0,
            )
            put.raise_for_status()
            client.mark_done(content_hash, audio_key=audio_key, owner=owner)
            typer.secho(f"Completed {content_hash}", fg=typer.colors.GREEN)
            processed = True
            if once is True:
                return

        if once is True:
            if not processed:
                typer.echo("No claimable jobs.")
            return
        time.sleep(poll_interval)
