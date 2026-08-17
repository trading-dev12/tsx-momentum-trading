"""
Northstar Quant
Mean Reversion Market Guard Research

Persists the relationship between the raw Mean Reversion
strategy decision and the separate broad-market entry guard.

Research only. This module never changes strategy decisions,
queue eligibility, positions, sizing, stops, targets or exits.
"""

from __future__ import annotations

import csv
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path


SCHEMA_VERSION = 1

DEFAULT_OUTPUT_DIRECTORY = Path(
    "data/runtime/mean_reversion_guard_results"
)


FIELDNAMES = [
    "schema_version",
    "captured_at_utc",
    "strategy",
    "signal_date",
    "symbol",
    "raw_decision",
    "queue_decision_after_guard",
    "raw_ready",
    "queue_eligible_after_guard",
    "guard_applicable_to_candidate",
    "guard_evaluated",
    "allow_new_entries",
    "market_guard_status",
    "market_regime",
    "guard_blocked_ready",
    "market_guard_reason",
    "raw_reason",
    "close",
    "tmqs",
    "rvol",
]


def _text(value):
    return str(
        value
        if value is not None
        else ""
    ).strip()


def _captured_at_text(
    captured_at=None,
):
    if captured_at is None:
        captured_at = datetime.now(
            timezone.utc
        )

    if isinstance(
        captured_at,
        datetime,
    ):
        if captured_at.tzinfo is None:
            captured_at = (
                captured_at.replace(
                    tzinfo=timezone.utc
                )
            )

        return (
            captured_at
            .astimezone(
                timezone.utc
            )
            .isoformat()
        )

    return _text(
        captured_at
    )


def build_mean_reversion_guard_rows(
    raw_results,
    guarded_result,
    measurement_date,
    captured_at=None,
):
    """
    Build one research row for every evaluated raw candidate.

    The raw strategy decision remains unchanged.

    For READY signals only:
    - PASS means the signal remains queue-eligible.
    - BLOCKED means the signal becomes WATCH for queue purposes.

    WATCH/IGNORE signals were never eligible for entry, so the
    guard is recorded for context without pretending it changed
    their raw strategy decision.
    """

    guard = (
        guarded_result.get(
            "guard",
            {},
        )
        if isinstance(
            guarded_result,
            dict,
        )
        else {}
    )

    guard_status = _text(
        guard.get(
            "guard_status"
        )
    ).upper()

    market_regime = _text(
        guard.get(
            "market_regime"
        )
    ).upper()

    guard_reason = _text(
        guard.get(
            "reason"
        )
    )

    allow_new_entries = guard.get(
        "allow_new_entries"
    )

    guard_evaluated = (
        guard_status
        not in {
            "",
            "NOT_EVALUATED",
        }
    )

    timestamp = _captured_at_text(
        captured_at
    )

    rows = []

    for bucket in (
        "ready",
        "watch",
        "ignore",
    ):
        for candidate in raw_results.get(
            bucket,
            [],
        ):
            raw_decision = _text(
                candidate.get(
                    "decision",
                    bucket,
                )
            ).upper()

            raw_ready = (
                raw_decision
                == "READY"
            )

            guard_blocked_ready = (
                raw_ready
                and guard_evaluated
                and allow_new_entries
                is False
            )

            queue_eligible = (
                raw_ready
                and (
                    allow_new_entries
                    is True
                )
            )

            if guard_blocked_ready:
                queue_decision = "WATCH"

            else:
                queue_decision = (
                    raw_decision
                )

            rows.append(
                {
                    "schema_version": (
                        SCHEMA_VERSION
                    ),
                    "captured_at_utc": (
                        timestamp
                    ),
                    "strategy": (
                        "MEAN_REVERSION"
                    ),
                    "signal_date": (
                        _text(
                            candidate.get(
                                "signal_date"
                            )
                        )
                        or _text(
                            measurement_date
                        )
                    ),
                    "symbol": _text(
                        candidate.get(
                            "symbol"
                        )
                    ).upper(),
                    "raw_decision": (
                        raw_decision
                    ),
                    (
                        "queue_decision_after_guard"
                    ): queue_decision,
                    "raw_ready": (
                        raw_ready
                    ),
                    (
                        "queue_eligible_after_guard"
                    ): queue_eligible,
                    (
                        "guard_applicable_to_candidate"
                    ): raw_ready,
                    "guard_evaluated": (
                        guard_evaluated
                    ),
                    "allow_new_entries": (
                        allow_new_entries
                        if allow_new_entries
                        is not None
                        else ""
                    ),
                    "market_guard_status": (
                        guard_status
                    ),
                    "market_regime": (
                        market_regime
                    ),
                    "guard_blocked_ready": (
                        guard_blocked_ready
                    ),
                    "market_guard_reason": (
                        guard_reason
                    ),
                    "raw_reason": _text(
                        candidate.get(
                            "reason"
                        )
                    ),
                    "close": candidate.get(
                        "close",
                        candidate.get(
                            "price",
                            "",
                        ),
                    ),
                    "tmqs": candidate.get(
                        "tmqs",
                        "",
                    ),
                    "rvol": candidate.get(
                        "rvol",
                        "",
                    ),
                }
            )

    return rows


def save_mean_reversion_guard_research(
    raw_results,
    guarded_result,
    measurement_date,
    output_directory=(
        DEFAULT_OUTPUT_DIRECTORY
    ),
    captured_at=None,
):
    """
    Atomically persist the daily Mean Reversion guard record.
    """

    rows = build_mean_reversion_guard_rows(
        raw_results=raw_results,
        guarded_result=guarded_result,
        measurement_date=(
            measurement_date
        ),
        captured_at=captured_at,
    )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_directory
        / f"{measurement_date}.csv"
    )

    temporary_path = Path(
        str(output_path)
        + ".tmp"
    )

    with temporary_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    temporary_path.replace(
        output_path
    )

    blocked_ready_count = sum(
        1
        for row in rows
        if row[
            "guard_blocked_ready"
        ]
    )

    return {
        "success": True,
        "status": "SAVED",
        "report_path": str(
            output_path
        ),
        "rows_saved": len(
            rows
        ),
        "blocked_ready_count": (
            blocked_ready_count
        ),
    }
