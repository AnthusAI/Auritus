#!/usr/bin/env python3
"""Move stored Auritus jobs to the canonical SHA-256 content hash.

Earlier embeds keyed jobs by a 32-bit FNV-1a hash computed in the browser.
The API now computes the canonical hash itself (SHA-256 of normalized text,
voice ID, and TTS backend joined by NUL) and rejects any other.

The move has two phases so pages still running the old embed keep playing
until the new embed and API are released:

``copy``
    Write each finished job (``done`` or ``failed``) whose key is not
    canonical under its canonical key, keeping its audio and recording
    ``migrated_from``. The legacy row stays. Jobs still in flight are
    skipped because the fallback workflow and the Batch job token refer to
    their key. An existing canonical job is never overwritten.

``revoke-tokens``
    Remove the worker token from every finished job and from jobs stuck in
    flight past the fallback workflow's two-hour timeout. Job creation used
    to return it to any site-key caller; recent in-flight jobs keep theirs.

``remove-legacy``
    After the release, delete each legacy row whose canonical copy records
    ``migrated_from`` it.

Both phases are dry runs unless ``--apply`` is passed.

Usage::

    python3 scripts/migrate_content_hashes.py copy --table <JobsTable> [--apply]
    python3 scripts/migrate_content_hashes.py revoke-tokens --table <JobsTable> [--apply]
    python3 scripts/migrate_content_hashes.py remove-legacy --table <JobsTable> [--apply]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import boto3

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "cdk"
        / "lambdas"
        / "operator_auth_layer"
        / "python"
    ),
)

from auritus_content_hash import content_hash  # noqa: E402

FINISHED_STATUSES = ("done", "failed")
IN_FLIGHT_STATUSES = ("pending", "claimed")
FALLBACK_TIMEOUT = timedelta(hours=2)


@dataclass
class MigrationReport:
    """What a migration phase did, or would do, per job key."""

    copied: list[tuple[str, str]] = field(default_factory=list)
    removed: list[tuple[str, str]] = field(default_factory=list)
    already_canonical: list[str] = field(default_factory=list)
    in_flight: list[str] = field(default_factory=list)
    canonical_exists: list[tuple[str, str]] = field(default_factory=list)
    missing_text: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)
    revoked: list[str] = field(default_factory=list)


def copy_to_canonical(jobs_table: Any, *, apply: bool) -> MigrationReport:
    """Copy finished legacy-keyed jobs to their canonical content hash.

    :param jobs_table: A boto3 DynamoDB ``Table`` resource for the jobs table.
    :param apply: Write the copies; otherwise only report them.
    :returns: The migration report.
    """
    report = MigrationReport()
    for item in _scan(jobs_table):
        current = item["content_hash"]
        if item.get("migrated_from"):
            report.already_canonical.append(current)
            continue
        canonical = _canonical_for(item)
        if canonical is None:
            report.missing_text.append(current)
            continue
        if canonical == current:
            report.already_canonical.append(current)
            continue
        if item.get("status") not in FINISHED_STATUSES:
            report.in_flight.append(current)
            continue
        existing = jobs_table.get_item(Key={"content_hash": canonical}).get("Item")
        if existing:
            if existing.get("migrated_from") != current:
                report.canonical_exists.append((current, canonical))
            continue
        report.copied.append((current, canonical))
        if apply:
            jobs_table.put_item(
                Item={
                    **{key: value for key, value in item.items() if key != "job_token"},
                    "content_hash": canonical,
                    "migrated_from": current,
                },
                ConditionExpression="attribute_not_exists(content_hash)",
            )
    return report


def remove_legacy_rows(jobs_table: Any, *, apply: bool) -> MigrationReport:
    """Delete legacy rows whose canonical copy records it was migrated from them.

    :param jobs_table: A boto3 DynamoDB ``Table`` resource for the jobs table.
    :param apply: Delete the rows; otherwise only report them.
    :returns: The migration report.
    """
    report = MigrationReport()
    for item in _scan(jobs_table):
        current = item["content_hash"]
        if item.get("migrated_from"):
            continue
        canonical = _canonical_for(item)
        if canonical is None or canonical == current:
            continue
        copy = jobs_table.get_item(Key={"content_hash": canonical}).get("Item")
        if not copy or copy.get("migrated_from") != current:
            report.kept.append(current)
            continue
        report.removed.append((current, canonical))
        if apply:
            jobs_table.delete_item(
                Key={"content_hash": current},
                ConditionExpression="attribute_exists(content_hash)",
            )
    return report


def revoke_finished_job_tokens(
    jobs_table: Any, *, apply: bool, now: datetime | None = None
) -> MigrationReport:
    """Remove worker tokens that no legitimate worker can still hold.

    Job creation used to return the worker token to any site-key caller.
    Finished jobs never need it again, and a job still pending or claimed
    longer than the fallback workflow's two-hour timeout has no Batch worker
    left to use it. Recent in-flight jobs keep their token.

    :param jobs_table: A boto3 DynamoDB ``Table`` resource for the jobs table.
    :param apply: Remove the tokens; otherwise only report them.
    :param now: The current time; defaults to the system clock.
    :returns: The migration report.
    """
    report = MigrationReport()
    cutoff = (now or datetime.now(timezone.utc)) - FALLBACK_TIMEOUT
    for item in _scan(jobs_table):
        if "job_token" not in item:
            continue
        status = item.get("status")
        finished = status in FINISHED_STATUSES
        stale = status in IN_FLIGHT_STATUSES and _created_before(item, cutoff)
        if not finished and not stale:
            continue
        report.revoked.append(item["content_hash"])
        if apply:
            jobs_table.update_item(
                Key={"content_hash": item["content_hash"]},
                UpdateExpression="REMOVE job_token",
                ConditionExpression="#status = :status AND created_at = :created",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": status,
                    ":created": item.get("created_at", ""),
                },
            )
    return report


def _created_before(item: dict[str, Any], cutoff: datetime) -> bool:
    created = str(item.get("created_at") or "")
    try:
        created_at = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return created_at.replace(tzinfo=timezone.utc) < cutoff


def _canonical_for(item: dict[str, Any]) -> str | None:
    text = item.get("text")
    if not text:
        return None
    return content_hash(text, item.get("voice_id"), item.get("tts_backend"))


def _scan(jobs_table: Any):
    kwargs: dict[str, Any] = {}
    while True:
        page = jobs_table.scan(**kwargs)
        yield from page.get("Items") or []
        if "LastEvaluatedKey" not in page:
            return
        kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]


def main() -> None:
    """Run one migration phase from the command line and print the report."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("phase", choices=["copy", "revoke-tokens", "remove-legacy"])
    parser.add_argument("--table", required=True, help="DynamoDB jobs table name")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--apply", action="store_true", help="write the changes")
    args = parser.parse_args()
    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table)
    prefix = "" if args.apply else "would "
    if args.phase == "copy":
        report = copy_to_canonical(table, apply=args.apply)
        for current, canonical in report.copied:
            print(f"{prefix}copy: {current} -> {canonical}")
        for current in report.in_flight:
            print(f"skipped (in flight): {current}")
        for current, canonical in report.canonical_exists:
            print(f"skipped (canonical exists): {current} -> {canonical}")
        for current in report.missing_text:
            print(f"skipped (no text): {current}")
        print(
            f"{prefix}copy {len(report.copied)}; already canonical "
            f"{len(report.already_canonical)}; in flight {len(report.in_flight)}; "
            f"canonical exists {len(report.canonical_exists)}; "
            f"no text {len(report.missing_text)}"
        )
        return
    if args.phase == "revoke-tokens":
        report = revoke_finished_job_tokens(table, apply=args.apply)
        print(f"{prefix}revoke {len(report.revoked)} worker tokens")
        return
    report = remove_legacy_rows(table, apply=args.apply)
    for current, canonical in report.removed:
        print(f"{prefix}remove: {current} (copied to {canonical})")
    for current in report.kept:
        print(f"kept (no migrated copy): {current}")
    print(f"{prefix}remove {len(report.removed)}; kept {len(report.kept)}")


if __name__ == "__main__":
    main()
