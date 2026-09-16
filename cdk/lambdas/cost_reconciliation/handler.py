"""Reconcile estimated daily GPU cost against the actual AWS bill.

Every other cost figure Auritus reports is a modelled *estimate*: a flat
platform allowance, and a GPU cost computed from AWS Batch billed seconds
multiplied by a hand-maintained hourly rate card (see
``cdk/stacks/backend.py``'s ``DEFAULT_GPU_HOURLY_RATE_USD`` comment -- that
rate has never itself been checked against a real invoice). This Lambda is
the reconciliation step that closes that loop: once a day is far enough in
the past that AWS Cost Explorer's data for it is final, this fetches the
ACTUAL AWS spend for that day and compares it to the summed GPU cost
estimate, so an operator can see how far the rate card has drifted -- and,
eventually, correct it.

Scope and two load-bearing assumptions, stated here because getting either
wrong would make every number this Lambda produces misleading:

1. **Account-wide, not per-site.** AWS Cost Explorer has no way to
   attribute spend to an Auritus "site" -- there are no cost allocation
   tags for that, and adding real tag-based per-site billing is a
   substantially larger effort than this story covers. This Lambda does
   NOT fabricate a per-site split of the actual cost. Instead, the
   account-wide actual cost and variance are written to one sentinel row
   in the SAME ``AuritusCostRollups`` table used for real per-site rollups,
   keyed by the reserved ``site_id`` value ``"__account__"`` (real site ids
   are UUIDs minted by the router's ``_create_site``, so this string can
   never collide with a real site) and the real calendar ``date``.

2. **"All AWS spend on relevant services in this account" is attributed to
   Auritus.** Cost Explorer is filtered by SERVICE (AWS Batch and its
   underlying EC2 usage -- the only services this stack provisions that
   have volatile, hard-to-estimate-correctly cost; DynamoDB/Lambda/S3/
   CloudFront are all covered by the flat, already-modelled platform-cost
   estimate instead), not by a cost allocation tag scoped to this stack's
   resources specifically. That is correct ONLY if this AWS account runs
   nothing but the Auritus ``AuritusBackend`` stack -- the single-dedicated-
   account deployment model this project's own ``AGENTS.local.md``
   describes. Deployed into a shared/multi-tenant AWS account, this would
   silently attribute other workloads' Batch/EC2 spend to Auritus too. This
   assumption is NOT verified at runtime; it is a deliberate, documented
   scope limit of this story, not an accident.

Timing: a day is only reconciled once it closed at least 24 hours ago --
Cost Explorer's data for a day is not final immediately, so reconciling
sooner would measure API latency, not real variance. On every scheduled
run, this looks for every day within the last ``RECONCILIATION_LOOKBACK_DAYS``
days (inclusive of the most recent eligible day) that does not yet have
``reconciled_at`` set on its ``"__account__"`` row, and reconciles all of
them -- not just "yesterday" -- so a single missed or failed invocation
(a cold start, a throttled Cost Explorer call, a redeploy that skips a
scheduled tick) does not silently leave a permanent gap in the reconciled
history. The lookback is bounded rather than unbounded so a Cost Explorer
outage lasting longer than that window degrades to "some old days stay
unreconciled" rather than "every run rescans all of history forever".

Writes are ``SET``, not ``ADD``. A day's actual AWS cost is a *fact*
Cost Explorer reports back deterministically for a fixed, final
``TimePeriod`` -- not a contribution accumulated from multiple independent
callers the way ``gpu_cost_usd``/``platform_cost_usd`` are (see the
router's ``_record_rollup_contribution`` and batch_telemetry's
``_roll_up_gpu_cost`` for that accumulation pattern, and why it must use
``ADD`` guarded by a job-level idempotency flag). Re-running this Lambda
for the same day -- whether from a Lambda-level retry, an operator
re-invoking it by hand, or a redeploy re-triggering the schedule -- and
writing the same ``SET`` again reproduces exactly the same stored values.
That makes this handler naturally idempotent without needing the
flag-then-ADD dance the per-job rollup paths require.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

_logger = logging.getLogger()
_logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb")
# Cost Explorer is a global service with a single API endpoint that only
# exists in us-east-1, regardless of which region the rest of the stack (or
# this Lambda itself) runs in. Passing any other region_name to this client
# raises at call time -- this is not a style preference, it is the only
# region in which the `ce` API is served.
_ce = boto3.client("ce", region_name="us-east-1")

COST_ROLLUPS_TABLE = os.environ["COST_ROLLUPS_TABLE"]
COST_ROLLUPS_DATE_INDEX = os.environ.get(
    "COST_ROLLUPS_DATE_INDEX", "date-site_id-index"
)
VARIANCE_THRESHOLD_PERCENT = float(os.environ.get("variance_threshold_percent", "20"))
RECONCILIATION_LOOKBACK_DAYS = int(os.environ.get("RECONCILIATION_LOOKBACK_DAYS", "7"))

# The reserved site_id sentinel for the account-wide reconciliation row.
# Real site ids are UUID4 strings minted by the router's _create_site, so
# this literal can never collide with one.
ACCOUNT_SENTINEL_SITE_ID = "__account__"

# Cost Explorer data for a day is not considered final until this many
# hours after that day closes (i.e. after UTC midnight starting the next
# day). Reconciling sooner would measure Cost Explorer's own reporting
# latency, not real estimate-vs-actual variance.
COST_EXPLORER_FINALITY_HOURS = 24

# The AWS service names (Cost Explorer's own service dimension values) this
# reconciliation filters to. Batch itself does not appear as a distinct
# billable service in Cost Explorer -- Batch is a scheduler, and the actual
# spend it drives shows up under EC2 (the instances it launches). Filtering
# to just these two is the "GPU cost" side of the rate card: DynamoDB,
# Lambda, S3, and CloudFront spend is intentionally excluded here because
# that side of the estimate is the flat, already-modelled platform-cost
# allowance, not the volatile part this story reconciles.
RECONCILED_SERVICES = (
    "Amazon Elastic Compute Cloud - Compute",
    "AWS Batch",
)

_cost_rollups = _dynamodb.Table(COST_ROLLUPS_TABLE)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _most_recent_final_date(now: datetime) -> str:
    """Return the most recent ``YYYY-MM-DD`` date that closed >= 24h ago.

    A day "closes" at UTC midnight starting the next day. It becomes
    eligible for reconciliation ``COST_EXPLORER_FINALITY_HOURS`` after
    that. E.g. at any point during 2026-01-16 UTC, 2026-01-14 is always
    final (it closed at 2026-01-15T00:00Z, >= 24h before any time on
    2026-01-16); 2026-01-15 is final only from 2026-01-16T00:00Z onward,
    i.e. essentially all of 2026-01-16 -- so in practice this returns
    "yesterday" for nearly the entire day and "two days ago" only in the
    first instant after UTC midnight.

    :param now: The current UTC time.
    :returns: The most recent eligible date, ``YYYY-MM-DD``.
    """
    candidate = (now - timedelta(days=1)).date()
    while True:
        day_close = datetime(
            candidate.year, candidate.month, candidate.day, tzinfo=timezone.utc
        ) + timedelta(days=1)
        if now - day_close >= timedelta(hours=COST_EXPLORER_FINALITY_HOURS):
            return candidate.strftime("%Y-%m-%d")
        candidate -= timedelta(days=1)


def _is_reconciled(date: str) -> bool:
    """Return whether the ``__account__`` row for ``date`` already has ``reconciled_at``."""
    item = _cost_rollups.get_item(
        Key={"site_id": ACCOUNT_SENTINEL_SITE_ID, "date": date}
    ).get("Item")
    return bool(item and item.get("reconciled_at"))


def _dates_to_reconcile(now: datetime) -> list[str]:
    """Return every unreconciled, Cost-Explorer-final date within the lookback window.

    Rather than assume exactly one day (typically "yesterday") needs
    reconciling on any given run, this checks the actual state of the
    ``__account__`` rollup rows for every final day within
    ``RECONCILIATION_LOOKBACK_DAYS`` and reconciles whichever ones are
    still missing ``reconciled_at``. This makes a single missed or failed
    invocation self-healing on the next run, without ever looking back
    further than the bounded window (an unbounded catch-up could turn a
    long-lived Cost Explorer outage into an ever-growing backlog of API
    calls on every subsequent run).

    :param now: The current UTC time.
    :returns: Dates to reconcile, oldest first.
    """
    most_recent_final = _most_recent_final_date(now)
    most_recent_dt = datetime.strptime(most_recent_final, "%Y-%m-%d")
    candidates = [
        (most_recent_dt - timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(RECONCILIATION_LOOKBACK_DAYS)
    ]
    pending = [date for date in candidates if not _is_reconciled(date)]
    return sorted(pending)


def _fetch_actual_cost_usd(date: str) -> Decimal:
    """Fetch the actual UnblendedCost for the relevant services on ``date``.

    :param date: ``YYYY-MM-DD``. Cost Explorer's ``TimePeriod`` is a
        half-open ``[Start, End)`` range, so this queries
        ``[date, date + 1 day)`` to get exactly that one calendar day.
    :returns: Summed actual cost in USD across ``RECONCILIED_SERVICES``.
    """
    next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    response = _ce.get_cost_and_usage(
        TimePeriod={"Start": date, "End": next_day},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": list(RECONCILED_SERVICES),
            }
        },
    )
    total = Decimal("0")
    for result in response.get("ResultsByTime") or []:
        amount = result.get("Total", {}).get("UnblendedCost", {}).get("Amount")
        if amount is not None:
            total += Decimal(str(amount))
    return total


def _sum_estimated_gpu_cost_usd(date: str) -> Decimal:
    """Sum real per-site ``gpu_cost_usd`` for ``date``, excluding the sentinel row.

    Queries the ``date-site_id-index`` GSI -- the same index the router's
    ``_get_admin_costs`` uses for its "all sites" summary -- for every
    rollup row on ``date``, and sums ``gpu_cost_usd`` across every row
    EXCEPT ``ACCOUNT_SENTINEL_SITE_ID`` itself (which never receives
    per-job GPU cost contributions from the normal request path -- only
    this handler writes to it, and only the reconciliation fields below).

    :param date: ``YYYY-MM-DD``.
    :returns: The account-wide estimated GPU cost for that date.
    """
    total = Decimal("0")
    response = _cost_rollups.query(
        IndexName=COST_ROLLUPS_DATE_INDEX,
        KeyConditionExpression=Key("date").eq(date),
    )
    for row in response.get("Items") or []:
        if row.get("site_id") == ACCOUNT_SENTINEL_SITE_ID:
            continue
        total += row.get("gpu_cost_usd") or Decimal("0")
    return total


def _reconcile_date(date: str) -> dict[str, Any]:
    """Reconcile one date: fetch actual cost, sum the estimate, write the sentinel row.

    :param date: ``YYYY-MM-DD`` to reconcile. Caller guarantees this date
        is Cost-Explorer-final.
    :returns: A summary dict, also written to the ``__account__`` row.
    """
    actual_cost_usd = _fetch_actual_cost_usd(date)
    estimated_gpu_cost_usd = _sum_estimated_gpu_cost_usd(date)
    variance_usd = actual_cost_usd - estimated_gpu_cost_usd

    # "Out of tolerance" when the estimate is exactly zero: a zero estimate
    # with nonzero actual cost is itself a meaningful signal (e.g. no Batch
    # jobs were recorded that day, yet AWS billed real EC2/Batch spend --
    # a sign the estimate pipeline missed something entirely), not a case
    # to silently pass over for lack of a denominator. Treat it as out of
    # tolerance whenever actual cost is nonzero; a zero estimate against
    # zero actual cost is perfect agreement, not a divide-by-zero error.
    if estimated_gpu_cost_usd == 0:
        out_of_tolerance = actual_cost_usd != 0
    else:
        variance_ratio = abs(variance_usd) / estimated_gpu_cost_usd
        out_of_tolerance = variance_ratio > (
            Decimal(str(VARIANCE_THRESHOLD_PERCENT)) / Decimal("100")
        )

    reconciled_at = _utc_now_iso()

    _cost_rollups.update_item(
        Key={"site_id": ACCOUNT_SENTINEL_SITE_ID, "date": date},
        UpdateExpression=(
            "SET actual_cost_usd = :actual, "
            "estimated_gpu_cost_usd = :estimated, "
            "variance_usd = :variance, "
            "reconciled_at = :reconciled_at, "
            "out_of_tolerance = :out_of_tolerance, "
            "variance_threshold_percent = :threshold"
        ),
        ExpressionAttributeValues={
            ":actual": actual_cost_usd,
            ":estimated": estimated_gpu_cost_usd,
            ":variance": variance_usd,
            ":reconciled_at": reconciled_at,
            ":out_of_tolerance": bool(out_of_tolerance),
            ":threshold": Decimal(str(VARIANCE_THRESHOLD_PERCENT)),
        },
    )

    _logger.info(
        "cost_reconciliation_recorded date=%s actual_cost_usd=%s "
        "estimated_gpu_cost_usd=%s variance_usd=%s out_of_tolerance=%s",
        date,
        actual_cost_usd,
        estimated_gpu_cost_usd,
        variance_usd,
        out_of_tolerance,
    )

    return {
        "date": date,
        "actual_cost_usd": str(actual_cost_usd),
        "estimated_gpu_cost_usd": str(estimated_gpu_cost_usd),
        "variance_usd": str(variance_usd),
        "out_of_tolerance": bool(out_of_tolerance),
        "reconciled_at": reconciled_at,
    }


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Reconcile every unreconciled, Cost-Explorer-final day in the lookback window.

    :param event: EventBridge scheduled-rule event (unused; this handler
        determines its own target dates from the rollup table's state
        rather than from anything in the event).
    :param _context: Lambda context (unused).
    :returns: ``{"reconciled": [...]}``, one entry per date actually
        reconciled this invocation (may be empty if everything in the
        lookback window is already reconciled).
    """
    now = datetime.now(timezone.utc)
    dates = _dates_to_reconcile(now)

    if not dates:
        _logger.info("cost_reconciliation_nothing_pending")
        return {"reconciled": []}

    _logger.info("cost_reconciliation_pending_dates=%s", dates)

    results = [_reconcile_date(date) for date in dates]
    return {"reconciled": results}
