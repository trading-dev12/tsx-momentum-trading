"""
Northstar Quant
Momentum Daily Universe Research Snapshot

Preserves the complete authoritative Momentum EOD opportunity
set for later post-validation research.

This module is observational only. It never changes strategy
rules, decisions, queues, positions, portfolios, or execution.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path


MOMENTUM_RESEARCH_SCHEMA_VERSION = 1

DEFAULT_OUTPUT_DIRECTORY = Path(
    "research/momentum_results"
)

FIELDNAMES = [
    "schema_version",
    "captured_at_utc",
    "signal_date",
    "symbol",
    "strategy",
    "decision",
    "daily_rank",
    "capture_status",
    "error_message",
    "reason",
    "data_source",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "previous_open",
    "previous_high",
    "previous_low",
    "previous_close",
    "previous_volume",
    "gap_percent",
    "price_change_percent",
    "breakout_percent",
    "dollar_volume",
    "atr",
    "atr_percent",
    "tmqs",
    "rvol",
    "breakout",
    "breakout_score",
    "volume_score",
    "price_score",
]


def _numeric(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_momentum_universe_rows(
    results,
    signal_date,
    captured_at=None,
):
    """
    Convert one Momentum EOD result into a complete research set.

    READY, WATCH, IGNORE and ERROR symbols are all retained.
    Ranking is descriptive only and has no effect on execution.
    """

    if captured_at is None:
        captured_at_text = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    else:
        if getattr(
            captured_at,
            "tzinfo",
            None,
        ) is not None:
            captured_at = (
                captured_at.astimezone(
                    timezone.utc
                )
            )

        captured_at_text = (
            captured_at.isoformat()
        )

    candidates = []

    for bucket in (
        "ready",
        "watch",
        "ignore",
    ):
        for row in results.get(
            bucket,
            [],
        ):
            candidates.append(
                dict(row)
            )

    candidates.sort(
        key=lambda row: (
            -_numeric(
                row.get("tmqs")
            ),
            -_numeric(
                row.get("rvol")
            ),
            str(
                row.get(
                    "symbol",
                    "",
                )
            ),
        )
    )

    rows = []

    for daily_rank, source_row in enumerate(
        candidates,
        start=1,
    ):
        record = {
            field: source_row.get(
                field,
                "",
            )
            for field in FIELDNAMES
        }

        record.update(
            {
                "schema_version": (
                    MOMENTUM_RESEARCH_SCHEMA_VERSION
                ),
                "captured_at_utc": (
                    captured_at_text
                ),
                "signal_date": (
                    source_row.get(
                        "signal_date",
                        signal_date,
                    )
                ),
                "strategy": (
                    source_row.get(
                        "strategy",
                        "MOMENTUM",
                    )
                ),
                "daily_rank": daily_rank,
                "capture_status": "OK",
                "error_message": "",
            }
        )

        rows.append(record)

    for error in results.get(
        "errors",
        [],
    ):
        error_message = (
            error.get("error")
            or error.get("message")
            or error.get("reason")
            or "Unknown Momentum EOD error"
        )

        record = {
            field: ""
            for field in FIELDNAMES
        }

        record.update(
            {
                "schema_version": (
                    MOMENTUM_RESEARCH_SCHEMA_VERSION
                ),
                "captured_at_utc": (
                    captured_at_text
                ),
                "signal_date": signal_date,
                "symbol": error.get(
                    "symbol",
                    "UNKNOWN",
                ),
                "strategy": "MOMENTUM",
                "decision": "ERROR",
                "daily_rank": "",
                "capture_status": "ERROR",
                "error_message": (
                    error_message
                ),
                "reason": error_message,
            }
        )

        rows.append(record)

    return rows


def save_momentum_universe_snapshot(
    results,
    signal_date,
    captured_at=None,
    output_directory=DEFAULT_OUTPUT_DIRECTORY,
):
    """
    Atomically save one complete Momentum EOD universe snapshot.
    """

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = build_momentum_universe_rows(
        results=results,
        signal_date=signal_date,
        captured_at=captured_at,
    )

    output_path = (
        output_directory
        / f"{signal_date}.csv"
    )

    temporary_path = (
        output_directory
        / f"{signal_date}.csv.tmp"
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
        writer.writerows(rows)

    temporary_path.replace(
        output_path
    )

    error_count = sum(
        1
        for row in rows
        if row.get(
            "capture_status"
        ) == "ERROR"
    )

    return {
        "success": True,
        "status": "CAPTURED",
        "report_path": str(
            output_path
        ),
        "rows_saved": len(rows),
        "error_rows": error_count,
    }
