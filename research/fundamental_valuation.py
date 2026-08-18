"""
Northstar Quant
Fundamental Valuation Research

Read-only valuation context for arbitrary TSX stocks.

The module compares current valuation multiples with the
recent historical valuation snapshots available from Yahoo.

It does not produce a BUY signal and does not alter any
Northstar strategy, scanner, queue, portfolio, or validation
sample.
"""

from __future__ import annotations

import math

import pandas as pd
import yfinance as yf


VALUATION_METRICS = {
    "Trailing P/E": "trailing_pe",
    "Forward P/E": "forward_pe",
    "Price/Sales": "price_sales",
    "Price/Book": "price_book",
    "Enterprise Value/Revenue": (
        "ev_revenue"
    ),
    "Enterprise Value/EBITDA": (
        "ev_ebitda"
    ),
}


def _positive_number(value):
    """
    Return a finite positive float or None.

    Negative/zero valuation multiples are not treated as
    comparable bargain multiples.
    """

    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if (
        not math.isfinite(number)
        or number <= 0
    ):
        return None

    return number


def classify_vs_recent_median(
    percent_difference,
):
    """
    Descriptive comparison with recent valuation history.

    These labels are research context only, not trading rules.
    """

    if percent_difference <= -20:
        return (
            "WELL_BELOW_RECENT_MEDIAN"
        )

    if percent_difference <= -10:
        return (
            "BELOW_RECENT_MEDIAN"
        )

    if percent_difference < 10:
        return (
            "NEAR_RECENT_MEDIAN"
        )

    if percent_difference < 20:
        return (
            "ABOVE_RECENT_MEDIAN"
        )

    return (
        "WELL_ABOVE_RECENT_MEDIAN"
    )


def load_valuation_measures(
    symbol,
):
    """
    Retrieve Yahoo's valuation-measures table.
    """

    ticker = yf.Ticker(
        symbol
    )

    return (
        ticker.get_valuation_measures()
    )


def _extract_current_value(
    table,
    row_name,
):
    if (
        row_name not in table.index
        or "Current" not in table.columns
    ):
        return None

    return _positive_number(
        table.loc[
            row_name,
            "Current",
        ]
    )


def _analyze_metric(
    table,
    row_name,
):
    """
    Compare one current multiple with available prior snapshots.
    """

    current = _extract_current_value(
        table,
        row_name,
    )

    if current is None:
        return {
            "current": None,
            "recent_median": None,
            "vs_recent_median_percent": (
                None
            ),
            "context": "UNAVAILABLE",
            "history_points": 0,
        }

    historical_values = []

    for column in table.columns:
        if str(column) == "Current":
            continue

        if row_name not in table.index:
            continue

        value = _positive_number(
            table.loc[
                row_name,
                column,
            ]
        )

        if value is not None:
            historical_values.append(
                value
            )

    if len(historical_values) < 2:
        return {
            "current": round(
                current,
                4,
            ),
            "recent_median": None,
            "vs_recent_median_percent": (
                None
            ),
            "context": (
                "INSUFFICIENT_HISTORY"
            ),
            "history_points": len(
                historical_values
            ),
        }

    recent_median = float(
        pd.Series(
            historical_values,
            dtype=float,
        ).median()
    )

    percent_difference = (
        (
            current
            - recent_median
        )
        / recent_median
        * 100.0
    )

    return {
        "current": round(
            current,
            4,
        ),
        "recent_median": round(
            recent_median,
            4,
        ),
        "vs_recent_median_percent": round(
            percent_difference,
            2,
        ),
        "context": (
            classify_vs_recent_median(
                percent_difference
            )
        ),
        "history_points": len(
            historical_values
        ),
    }


def classify_overall_valuation(
    metric_results,
):
    """
    Summarize the direction of the available evidence.

    Deliberately avoids creating a numeric valuation score.
    """

    below_states = {
        "BELOW_RECENT_MEDIAN",
        "WELL_BELOW_RECENT_MEDIAN",
    }

    above_states = {
        "ABOVE_RECENT_MEDIAN",
        "WELL_ABOVE_RECENT_MEDIAN",
    }

    below_count = sum(
        result.get("context")
        in below_states
        for result
        in metric_results.values()
    )

    above_count = sum(
        result.get("context")
        in above_states
        for result
        in metric_results.values()
    )

    near_count = sum(
        result.get("context")
        == "NEAR_RECENT_MEDIAN"
        for result
        in metric_results.values()
    )

    comparable_count = (
        below_count
        + above_count
        + near_count
    )

    if comparable_count == 0:
        context = (
            "INSUFFICIENT_HISTORY"
        )

    elif (
        below_count >= 2
        and above_count >= 2
    ):
        context = "MIXED"

    elif (
        below_count >= 3
        and above_count == 0
    ):
        context = (
            "BELOW_RECENT_HISTORY"
        )

    elif (
        above_count >= 3
        and below_count == 0
    ):
        context = (
            "ABOVE_RECENT_HISTORY"
        )

    elif below_count > above_count:
        context = (
            "LEANING_BELOW_RECENT_HISTORY"
        )

    elif above_count > below_count:
        context = (
            "LEANING_ABOVE_RECENT_HISTORY"
        )

    else:
        context = (
            "NEAR_RECENT_HISTORY"
        )

    return {
        "context": context,
        "below_recent_count": (
            below_count
        ),
        "above_recent_count": (
            above_count
        ),
        "near_recent_count": (
            near_count
        ),
        "comparable_metric_count": (
            comparable_count
        ),
    }


def calculate_fundamental_valuation(
    symbol,
    valuation_provider=(
        load_valuation_measures
    ),
):
    """
    Build read-only fundamental valuation context.
    """

    normalized_symbol = str(
        symbol or ""
    ).strip().upper()

    if not normalized_symbol:
        return {
            "status": "UNAVAILABLE",
            "reason": (
                "Symbol is required."
            ),
        }

    try:
        table = valuation_provider(
            normalized_symbol
        )

        if (
            table is None
            or not isinstance(
                table,
                pd.DataFrame,
            )
            or table.empty
        ):
            raise ValueError(
                "No valuation measures were returned."
            )

        if "Current" not in table.columns:
            raise ValueError(
                "Valuation table has no Current column."
            )

        metric_results = {}

        for (
            row_name,
            output_name,
        ) in VALUATION_METRICS.items():
            metric_results[
                output_name
            ] = _analyze_metric(
                table,
                row_name,
            )

        available_metric_count = sum(
            result.get("current")
            is not None
            for result
            in metric_results.values()
        )

        overall = (
            classify_overall_valuation(
                metric_results
            )
        )

        historical_columns = [
            str(column)
            for column in table.columns
            if str(column) != "Current"
        ]

        market_cap = (
            _extract_current_value(
                table,
                "Market Cap",
            )
        )

        enterprise_value = (
            _extract_current_value(
                table,
                "Enterprise Value",
            )
        )

        return {
            "symbol": (
                normalized_symbol
            ),
            "status": (
                "AVAILABLE"
                if available_metric_count
                else "UNAVAILABLE"
            ),
            "reason": (
                ""
                if available_metric_count
                else (
                    "No usable current "
                    "valuation multiples."
                )
            ),
            "data_source": (
                "YAHOO_VALUATION_MEASURES"
            ),
            "valuation_context": (
                overall["context"]
            ),
            "available_metric_count": (
                available_metric_count
            ),
            "comparable_metric_count": (
                overall[
                    "comparable_metric_count"
                ]
            ),
            "below_recent_count": (
                overall[
                    "below_recent_count"
                ]
            ),
            "above_recent_count": (
                overall[
                    "above_recent_count"
                ]
            ),
            "near_recent_count": (
                overall[
                    "near_recent_count"
                ]
            ),
            "history_snapshot_count": len(
                historical_columns
            ),
            "history_snapshots": (
                historical_columns
            ),
            "market_cap": (
                round(
                    market_cap,
                    2,
                )
                if market_cap is not None
                else None
            ),
            "enterprise_value": (
                round(
                    enterprise_value,
                    2,
                )
                if enterprise_value
                is not None
                else None
            ),
            "metrics": metric_results,
            "research_only": True,
            "interpretation_note": (
                "Lower positive valuation "
                "multiples are treated as "
                "cheaper relative to the "
                "stock's own recent history. "
                "This is not a BUY signal."
            ),
        }

    except Exception as error:
        return {
            "symbol": (
                normalized_symbol
            ),
            "status": "UNAVAILABLE",
            "reason": str(
                error
            ),
            "data_source": (
                "YAHOO_VALUATION_MEASURES"
            ),
            "research_only": True,
        }
