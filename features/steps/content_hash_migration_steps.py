"""Step definitions for re-keying stored jobs to the canonical content hash."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from behave import given, then, when
from common_steps import _hash

from support.router_harness import start_router

MIGRATION_SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "migrate_content_hashes.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location(
        "migrate_content_hashes", MIGRATION_SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _jobs(context):
    if not hasattr(context, "migration_harness"):
        context.migration_harness = start_router(context)
    return context.migration_harness.jobs_table


def _job(context, content_hash: str):
    return _jobs(context).get_item(Key={"content_hash": content_hash}).get("Item")


@given(
    'a "{status}" job stored under the legacy hash "{legacy_hash}" '
    'with text "{text}" and {audio}'
)
def step_legacy_job(
    context, status: str, legacy_hash: str, text: str, audio: str
) -> None:
    item = {
        "content_hash": legacy_hash,
        "status": status,
        "text": text,
        "voice_id": "af_heart",
        "tts_backend": "kokoro",
        "site_id": "site-migration",
        "job_token": "legacy-job-token",
        "created_at": "2026-09-01T00:00:00Z",
    }
    if audio == "stored audio":
        item["audio_key"] = f"audio/{legacy_hash}.wav"
    _jobs(context).put_item(Item=item)
    context.legacy_text = text


@given('a "{status}" job already stored under the canonical hash of "{text}"')
def step_canonical_job(context, status: str, text: str) -> None:
    context.canonical_item = {
        "content_hash": _hash(text, "af_heart", "kokoro"),
        "status": status,
        "text": text,
        "voice_id": "af_heart",
        "tts_backend": "kokoro",
        "audio_key": "audio/already-canonical.wav",
        "created_at": "2026-09-20T00:00:00Z",
    }
    _jobs(context).put_item(Item=context.canonical_item)


@given("the content hash copy has run with apply")
def step_copy_has_run(context) -> None:
    _load_migration().copy_to_canonical(_jobs(context), apply=True)


@when("the content hash copy runs {mode}")
def step_run_copy(context, mode: str) -> None:
    context.migration_report = _load_migration().copy_to_canonical(
        _jobs(context), apply=(mode == "with apply")
    )


@when("the legacy row removal runs with apply")
def step_run_removal(context) -> None:
    context.migration_report = _load_migration().remove_legacy_rows(
        _jobs(context), apply=True
    )


@then('the job is stored under the canonical hash of "{text}"')
def step_job_under_canonical(context, text: str) -> None:
    context.migrated_item = _job(context, _hash(text, "af_heart", "kokoro"))
    assert context.migrated_item is not None, context.migration_report


@then(
    "the migrated job keeps its audio and records it was migrated from "
    '"{legacy_hash}"'
)
def step_migrated_keeps_audio(context, legacy_hash: str) -> None:
    item = context.migrated_item
    assert item["audio_key"] == f"audio/{legacy_hash}.wav", item
    assert item["status"] == "done", item
    assert item["migrated_from"] == legacy_hash, item


@then('no job is stored under "{content_hash}"')
def step_no_job_under(context, content_hash: str) -> None:
    assert _job(context, content_hash) is None


@then('a job is still stored under "{content_hash}"')
def step_job_still_under(context, content_hash: str) -> None:
    assert _job(context, content_hash) is not None


@then("the migration reports {count:d} job to copy")
def step_report_copy(context, count: int) -> None:
    assert len(context.migration_report.copied) == count, context.migration_report


@then('no job is stored under the canonical hash of "{text}"')
def step_no_canonical_job(context, text: str) -> None:
    assert _job(context, _hash(text, "af_heart", "kokoro")) is None


@then("the migration reports {count:d} job skipped as in flight")
def step_report_in_flight(context, count: int) -> None:
    assert len(context.migration_report.in_flight) == count, context.migration_report


@then("the migration reports {count:d} job skipped as already canonical elsewhere")
def step_report_conflict(context, count: int) -> None:
    assert (
        len(context.migration_report.canonical_exists) == count
    ), context.migration_report


@then("the canonical job is unchanged")
def step_canonical_unchanged(context) -> None:
    item = _job(context, context.canonical_item["content_hash"])
    assert item == context.canonical_item, item
