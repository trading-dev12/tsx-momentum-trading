import math

import pandas as pd

from research.fundamental_valuation import (
    calculate_fundamental_valuation,
    classify_vs_recent_median,
)


def make_table(
    current_values,
    history_values,
):
    columns = [
        "Current",
        "2026-Q2",
        "2026-Q1",
        "2025-Q4",
        "2025-Q3",
        "2025-Q2",
    ]

    rows = {}

    for metric, current in (
        current_values.items()
    ):
        rows[metric] = [
            current,
            *history_values[metric],
        ]

    rows["Market Cap"] = [
        50_000_000_000,
        45_000_000_000,
        44_000_000_000,
        43_000_000_000,
        42_000_000_000,
        41_000_000_000,
    ]

    rows["Enterprise Value"] = [
        55_000_000_000,
        50_000_000_000,
        49_000_000_000,
        48_000_000_000,
        47_000_000_000,
        46_000_000_000,
    ]

    return pd.DataFrame.from_dict(
        rows,
        orient="index",
        columns=columns,
    )


def test_metric_comparison_labels():
    assert (
        classify_vs_recent_median(
            -25
        )
        == "WELL_BELOW_RECENT_MEDIAN"
    )

    assert (
        classify_vs_recent_median(
            -12
        )
        == "BELOW_RECENT_MEDIAN"
    )

    assert (
        classify_vs_recent_median(
            3
        )
        == "NEAR_RECENT_MEDIAN"
    )

    assert (
        classify_vs_recent_median(
            14
        )
        == "ABOVE_RECENT_MEDIAN"
    )

    assert (
        classify_vs_recent_median(
            30
        )
        == "WELL_ABOVE_RECENT_MEDIAN"
    )


def test_mixed_valuation_is_preserved():
    current = {
        "Trailing P/E": 12.0,
        "Forward P/E": 10.0,
        "Price/Sales": 2.0,
        "Price/Book": 3.0,
        "Enterprise Value/Revenue": 2.2,
        "Enterprise Value/EBITDA": 6.0,
    }

    history = {
        "Trailing P/E": [
            15, 15, 15, 15, 15
        ],
        "Forward P/E": [
            15, 15, 15, 15, 15
        ],
        "Price/Sales": [
            1, 1, 1, 1, 1
        ],
        "Price/Book": [
            2, 2, 2, 2, 2
        ],
        "Enterprise Value/Revenue": [
            1.5, 1.5, 1.5, 1.5, 1.5
        ],
        "Enterprise Value/EBITDA": [
            6, 6, 6, 6, 6
        ],
    }

    table = make_table(
        current,
        history,
    )

    def provider(symbol):
        return table

    result = (
        calculate_fundamental_valuation(
            "TEST.TO",
            valuation_provider=provider,
        )
    )

    assert (
        result["status"]
        == "AVAILABLE"
    )

    assert (
        result["valuation_context"]
        == "MIXED"
    )

    assert (
        result["below_recent_count"]
        == 2
    )

    assert (
        result["above_recent_count"]
        == 3
    )

    assert (
        result["near_recent_count"]
        == 1
    )

    assert (
        result["research_only"]
        is True
    )


def test_broadly_cheaper_valuation_is_identified():
    current = {
        "Trailing P/E": 8,
        "Forward P/E": 8,
        "Price/Sales": 0.8,
        "Price/Book": 1.2,
        "Enterprise Value/Revenue": 0.8,
        "Enterprise Value/EBITDA": 4,
    }

    history = {
        metric: [
            10, 10, 10, 10, 10
        ]
        for metric
        in current
    }

    table = make_table(
        current,
        history,
    )

    def provider(symbol):
        return table

    result = (
        calculate_fundamental_valuation(
            "CHEAP.TO",
            valuation_provider=provider,
        )
    )

    assert (
        result["valuation_context"]
        == "BELOW_RECENT_HISTORY"
    )

    assert (
        result["below_recent_count"]
        >= 3
    )


def test_nan_metric_does_not_break_report():
    current = {
        "Trailing P/E": 12,
        "Forward P/E": math.nan,
        "Price/Sales": 1.1,
        "Price/Book": 1.5,
        "Enterprise Value/Revenue": 1.0,
        "Enterprise Value/EBITDA": 5.0,
    }

    history = {
        metric: [
            12, 12, 12, 12, 12
        ]
        for metric
        in current
    }

    table = make_table(
        current,
        history,
    )

    def provider(symbol):
        return table

    result = (
        calculate_fundamental_valuation(
            "ABC.TO",
            valuation_provider=provider,
        )
    )

    assert (
        result["status"]
        == "AVAILABLE"
    )

    assert (
        result["metrics"][
            "forward_pe"
        ]["current"]
        is None
    )

    assert (
        result["available_metric_count"]
        == 5
    )


def test_provider_failure_is_fail_soft():
    def provider(symbol):
        raise RuntimeError(
            "Yahoo unavailable"
        )

    result = (
        calculate_fundamental_valuation(
            "ABC.TO",
            valuation_provider=provider,
        )
    )

    assert (
        result["status"]
        == "UNAVAILABLE"
    )

    assert (
        "Yahoo unavailable"
        in result["reason"]
    )

    assert (
        result["research_only"]
        is True
    )
