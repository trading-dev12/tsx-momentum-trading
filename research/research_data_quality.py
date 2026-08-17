"""
Northstar Quant
Research Data Source Quality

Read-only audit of which market-data source supplied
each completed trade's research factors.

This module never changes trading rules, journals,
positions, signals, or portfolios.
"""

import csv
import json
from datetime import date
from pathlib import Path

from research.enrichment_integrity import (
    CAPTURE_MONITOR_START_DATE,
)


SOURCE_FIELDS = {
    "Relative Strength": "rs_data_source",
    "Market Regime": "market_regime_data_source",
    "Moving Average": "ma_data_source",
    "Gap Analysis": "gap_data_source",
    "Sector Strength": "sector_strength_data_source",
    "Volatility": "volatility_data_source",
}


CAPTURE_SOURCE_FIELDS = {
    "Signal Snapshot": (None, None),
    "Entry Fill": (
        "price_source",
        None,
    ),
    "Entry Quote": (
        "entry_quote_source",
        "entry_quote_status",
    ),
    "Exit Quote": (
        "exit_quote_source",
        "exit_quote_status",
    ),
    "Trade Path": (
        "trade_path_source",
        "trade_path_status",
    ),
}


SIGNAL_SNAPSHOT_SOURCE_KEYS = (
    "data_source",
    "signal_data_source",
    "price_source",
    "live_data_source",
)


def _parse_entry_date(value):
    text = str(
        value or ""
    ).strip()

    if not text:
        return None

    try:
        return date.fromisoformat(
            text
        )

    except ValueError:
        return None


def _classify_source(value):
    text = str(
        value or ""
    ).strip()

    upper = text.upper()

    if not text:
        return "missing"

    if upper.startswith("IBKR"):
        return "ibkr"

    if "FALLBACK" in upper:
        return "fallback"

    return "other"


def _signal_snapshot_source(row):
    raw = str(
        row.get(
            "signal_snapshot_json",
            "",
        )
        or ""
    ).strip()

    if not raw:
        return ""

    try:
        snapshot = json.loads(
            raw
        )

    except (
        TypeError,
        ValueError,
    ):
        return ""

    if not isinstance(
        snapshot,
        dict,
    ):
        return ""

    for key in (
        SIGNAL_SNAPSHOT_SOURCE_KEYS
    ):
        source = str(
            snapshot.get(
                key,
                "",
            )
            or ""
        ).strip()

        if source:
            return source

    return ""


def _calculate_capture_source_coverage(
    rows,
    monitor_start_date=(
        CAPTURE_MONITOR_START_DATE
    ),
):
    """
    Audit provenance for the newer 200-trade capture.

    This reports where the captured observations came from.
    It does not change trading or research data.
    """

    monitored_rows = []
    legacy_trade_count = 0
    undated_trade_count = 0

    for row in rows:
        entry_date = _parse_entry_date(
            row.get(
                "entry_date",
                "",
            )
        )

        if entry_date is None:
            undated_trade_count += 1
            continue

        if entry_date < monitor_start_date:
            legacy_trade_count += 1
            continue

        monitored_rows.append(
            row
        )

    monitored_trade_count = len(
        monitored_rows
    )

    factor_count = len(
        CAPTURE_SOURCE_FIELDS
    )

    possible = (
        monitored_trade_count
        * factor_count
    )

    factors = {}

    total_recorded = 0
    total_ibkr = 0
    total_fallback = 0
    total_other = 0

    for (
        factor_name,
        definition,
    ) in CAPTURE_SOURCE_FIELDS.items():

        source_field, status_field = (
            definition
        )

        recorded = 0
        ibkr = 0
        fallback = 0
        other = 0
        status_counts = {}

        for row in monitored_rows:

            if source_field is None:
                source = (
                    _signal_snapshot_source(
                        row
                    )
                )

            else:
                source = str(
                    row.get(
                        source_field,
                        "",
                    )
                    or ""
                ).strip()

            classification = (
                _classify_source(
                    source
                )
            )

            if classification != "missing":
                recorded += 1

            if classification == "ibkr":
                ibkr += 1

            elif classification == "fallback":
                fallback += 1

            elif classification == "other":
                other += 1

            if status_field:
                status = str(
                    row.get(
                        status_field,
                        "",
                    )
                    or ""
                ).strip().upper()

                status_counts[
                    status or "MISSING"
                ] = (
                    status_counts.get(
                        status or "MISSING",
                        0,
                    )
                    + 1
                )

        factors[factor_name] = {
            "source_field": source_field,
            "status_field": status_field,
            "recorded": recorded,
            "missing": (
                monitored_trade_count
                - recorded
            ),
            "ibkr": ibkr,
            "fallback": fallback,
            "other": other,
            "recorded_percent": round(
                (
                    recorded
                    / monitored_trade_count
                    * 100.0
                )
                if monitored_trade_count
                else 0.0,
                2,
            ),
            "ibkr_percent_of_recorded": round(
                (
                    ibkr
                    / recorded
                    * 100.0
                )
                if recorded
                else 0.0,
                2,
            ),
            "status_counts": status_counts,
        }

        total_recorded += recorded
        total_ibkr += ibkr
        total_fallback += fallback
        total_other += other

    complete_source_trade_count = 0

    for row in monitored_rows:
        sources = [
            _signal_snapshot_source(
                row
            ),
            row.get(
                "price_source",
                "",
            ),
            row.get(
                "entry_quote_source",
                "",
            ),
            row.get(
                "exit_quote_source",
                "",
            ),
            row.get(
                "trade_path_source",
                "",
            ),
        ]

        if all(
            str(
                source or ""
            ).strip()
            for source in sources
        ):
            complete_source_trade_count += 1

    missing = (
        possible
        - total_recorded
    )

    if monitored_trade_count == 0:
        status = (
            "NO_MONITORED_TRADES_YET"
        )

    elif total_recorded == 0:
        status = (
            "SOURCE_TRACKING_NOT_YET_RECORDED"
        )

    elif total_recorded < possible:
        status = (
            "PARTIAL_CAPTURE_SOURCE_HISTORY"
        )

    else:
        status = (
            "COMPLETE_CAPTURE_SOURCE_HISTORY"
        )

    return {
        "monitor_start_date": (
            monitor_start_date.isoformat()
        ),
        "monitored_trade_count": (
            monitored_trade_count
        ),
        "legacy_trade_count": (
            legacy_trade_count
        ),
        "undated_trade_count": (
            undated_trade_count
        ),
        "factor_count": factor_count,
        "possible_source_observations": (
            possible
        ),
        "recorded_source_observations": (
            total_recorded
        ),
        "missing_source_observations": (
            missing
        ),
        "ibkr_source_observations": (
            total_ibkr
        ),
        "fallback_source_observations": (
            total_fallback
        ),
        "other_source_observations": (
            total_other
        ),
        "recorded_coverage_percent": round(
            (
                total_recorded
                / possible
                * 100.0
            )
            if possible
            else 0.0,
            2,
        ),
        "ibkr_percent_of_recorded": round(
            (
                total_ibkr
                / total_recorded
                * 100.0
            )
            if total_recorded
            else 0.0,
            2,
        ),
        "complete_source_trade_count": (
            complete_source_trade_count
        ),
        "status": status,
        "factors": factors,
    }


def _load_rows(file_path):
    """
    Read a paper trade journal without modifying it.
    """

    path = Path(file_path)

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def calculate_research_source_coverage(file_path):
    """
    Calculate research market-data source coverage.

    Older trades may legitimately have blank source fields
    because source auditing did not yet exist.

    Percentages therefore distinguish:

    1. How much of the possible source history was recorded.
    2. How much of the recorded history used IBKR.
    """

    rows = _load_rows(
        file_path
    )

    trade_count = len(
        rows
    )

    factor_count = len(
        SOURCE_FIELDS
    )

    possible_observations = (
        trade_count
        * factor_count
    )

    factor_results = {}

    total_recorded = 0
    total_ibkr = 0
    total_fallback = 0
    total_other = 0

    for (
        factor_name,
        field_name,
    ) in SOURCE_FIELDS.items():

        recorded = 0
        ibkr = 0
        fallback = 0
        other = 0

        for row in rows:
            source = str(
                row.get(
                    field_name,
                    "",
                )
                or ""
            ).strip()

            if not source:
                continue

            recorded += 1

            if source.startswith(
                "IBKR"
            ):
                ibkr += 1

            elif (
                "FALLBACK"
                in source.upper()
            ):
                fallback += 1

            else:
                other += 1

        missing = (
            trade_count
            - recorded
        )

        recorded_percent = (
            (
                recorded
                / trade_count
            )
            * 100
            if trade_count
            else 0.0
        )

        ibkr_percent_of_recorded = (
            (
                ibkr
                / recorded
            )
            * 100
            if recorded
            else 0.0
        )

        factor_results[
            factor_name
        ] = {
            "field": field_name,
            "recorded": recorded,
            "missing": missing,
            "ibkr": ibkr,
            "fallback": fallback,
            "other": other,
            "recorded_percent": round(
                recorded_percent,
                2,
            ),
            "ibkr_percent_of_recorded": round(
                ibkr_percent_of_recorded,
                2,
            ),
        }

        total_recorded += recorded
        total_ibkr += ibkr
        total_fallback += fallback
        total_other += other

    missing_observations = (
        possible_observations
        - total_recorded
    )

    recorded_coverage_percent = (
        (
            total_recorded
            / possible_observations
        )
        * 100
        if possible_observations
        else 0.0
    )

    ibkr_percent_of_recorded = (
        (
            total_ibkr
            / total_recorded
        )
        * 100
        if total_recorded
        else 0.0
    )

    capture_sources = (
        _calculate_capture_source_coverage(
            rows
        )
    )

    if trade_count == 0:
        status = "NO_TRADES"

    elif total_recorded == 0:
        status = (
            "SOURCE_TRACKING_NOT_YET_RECORDED"
        )

    elif (
        total_recorded
        < possible_observations
    ):
        status = (
            "PARTIAL_SOURCE_HISTORY"
        )

    else:
        status = (
            "COMPLETE_SOURCE_HISTORY"
        )

    return {
        "trade_count": trade_count,
        "factor_count": factor_count,
        "possible_source_observations": (
            possible_observations
        ),
        "recorded_source_observations": (
            total_recorded
        ),
        "missing_source_observations": (
            missing_observations
        ),
        "ibkr_source_observations": (
            total_ibkr
        ),
        "fallback_source_observations": (
            total_fallback
        ),
        "other_source_observations": (
            total_other
        ),
        "recorded_coverage_percent": round(
            recorded_coverage_percent,
            2,
        ),
        "ibkr_percent_of_recorded": round(
            ibkr_percent_of_recorded,
            2,
        ),
        "status": status,
        "factors": factor_results,
        "capture_sources": (
            capture_sources
        ),
    }
