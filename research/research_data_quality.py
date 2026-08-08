"""
Northstar Quant
Research Data Source Quality

Read-only audit of which market-data source supplied
each completed trade's research factors.

This module never changes trading rules, journals,
positions, signals, or portfolios.
"""

import csv
from pathlib import Path


SOURCE_FIELDS = {
    "Relative Strength": "rs_data_source",
    "Market Regime": "market_regime_data_source",
    "Moving Average": "ma_data_source",
    "Gap Analysis": "gap_data_source",
    "Sector Strength": "sector_strength_data_source",
    "Volatility": "volatility_data_source",
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
    }
