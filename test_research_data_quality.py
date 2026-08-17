import csv
import json

from research.research_data_quality import (
    calculate_research_source_coverage,
)


def test_research_source_coverage(tmp_path):
    journal = (
        tmp_path
        / "journal.csv"
    )

    fieldnames = [
        "symbol",
        "rs_data_source",
        "market_regime_data_source",
        "ma_data_source",
        "gap_data_source",
        "sector_strength_data_source",
        "volatility_data_source",
    ]

    rows = [
        {
            "symbol": "AAA.TO",
            "rs_data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
            "market_regime_data_source": (
                "IBKR_TRADES"
            ),
            "ma_data_source": (
                "IBKR_TRADES"
            ),
            "gap_data_source": (
                "IBKR_TRADES"
            ),
            "sector_strength_data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
            "volatility_data_source": (
                "IBKR_TRADES"
            ),
        },
        {
            "symbol": "BBB.TO",
            "rs_data_source": (
                "LOCAL_ADJUSTED_FALLBACK"
            ),
            "market_regime_data_source": (
                "IBKR_TRADES"
            ),
            "ma_data_source": "",
            "gap_data_source": (
                "YAHOO_FALLBACK"
            ),
            "sector_strength_data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
            "volatility_data_source": (
                "IBKR_TRADES"
            ),
        },
    ]

    with journal.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    result = (
        calculate_research_source_coverage(
            journal
        )
    )

    assert result[
        "trade_count"
    ] == 2

    assert result[
        "possible_source_observations"
    ] == 12

    assert result[
        "recorded_source_observations"
    ] == 11

    assert result[
        "ibkr_source_observations"
    ] == 9

    assert result[
        "fallback_source_observations"
    ] == 2

    assert result[
        "missing_source_observations"
    ] == 1

    assert result[
        "recorded_coverage_percent"
    ] == 91.67

    assert result[
        "ibkr_percent_of_recorded"
    ] == 81.82

    assert result[
        "status"
    ] == "PARTIAL_SOURCE_HISTORY"


def test_legacy_journal_without_source_columns(
    tmp_path,
):
    journal = (
        tmp_path
        / "legacy.csv"
    )

    journal.write_text(
        "symbol,profit_loss\n"
        "AAA.TO,10\n",
        encoding="utf-8",
    )

    result = (
        calculate_research_source_coverage(
            journal
        )
    )

    assert result[
        "trade_count"
    ] == 1

    assert result[
        "recorded_source_observations"
    ] == 0

    assert result[
        "status"
    ] == (
        "SOURCE_TRACKING_NOT_YET_RECORDED"
    )

def test_200_trade_capture_source_coverage(
    tmp_path,
):
    journal = (
        tmp_path
        / "capture_sources.csv"
    )

    fieldnames = [
        "symbol",
        "entry_date",
        "signal_snapshot_json",
        "price_source",
        "entry_quote_source",
        "entry_quote_status",
        "exit_quote_source",
        "exit_quote_status",
        "trade_path_source",
        "trade_path_status",
    ]

    rows = [
        {
            "symbol": "AAA.TO",
            "entry_date": "2026-08-18",
            "signal_snapshot_json": (
                json.dumps(
                    {
                        "data_source": (
                            "YAHOO_DAILY"
                        ),
                    }
                )
            ),
            "price_source": (
                "IBKR_ONE_MINUTE"
            ),
            "entry_quote_source": (
                "IBKR_LIVE"
            ),
            "entry_quote_status": (
                "AVAILABLE"
            ),
            "exit_quote_source": (
                "IBKR_LIVE"
            ),
            "exit_quote_status": (
                "AVAILABLE"
            ),
            "trade_path_source": (
                "IBKR_ONE_MINUTE"
            ),
            "trade_path_status": (
                "COMPLETE"
            ),
        },
        {
            "symbol": "BBB.TO",
            "entry_date": "2026-08-19",
            "signal_snapshot_json": (
                json.dumps(
                    {
                        "data_source": (
                            "YAHOO_DAILY"
                        ),
                    }
                )
            ),
            "price_source": (
                "YAHOO_ONE_MINUTE_FALLBACK"
            ),
            "entry_quote_source": (
                "YAHOO_FALLBACK"
            ),
            "entry_quote_status": (
                "UNAVAILABLE"
            ),
            "exit_quote_source": "",
            "exit_quote_status": (
                "UNAVAILABLE"
            ),
            "trade_path_source": (
                "IBKR_ONE_MINUTE"
            ),
            "trade_path_status": (
                "COMPLETE"
            ),
        },
    ]

    with journal.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )

    result = (
        calculate_research_source_coverage(
            journal
        )
    )

    capture = result[
        "capture_sources"
    ]

    assert (
        capture[
            "monitored_trade_count"
        ]
        == 2
    )

    assert capture["factor_count"] == 5

    assert (
        capture[
            "possible_source_observations"
        ]
        == 10
    )

    assert (
        capture[
            "recorded_source_observations"
        ]
        == 9
    )

    assert (
        capture[
            "missing_source_observations"
        ]
        == 1
    )

    assert (
        capture[
            "ibkr_source_observations"
        ]
        == 5
    )

    assert (
        capture[
            "fallback_source_observations"
        ]
        == 2
    )

    assert (
        capture[
            "other_source_observations"
        ]
        == 2
    )

    assert (
        capture[
            "recorded_coverage_percent"
        ]
        == 90.0
    )

    assert (
        capture[
            "complete_source_trade_count"
        ]
        == 1
    )

    assert (
        capture["status"]
        == "PARTIAL_CAPTURE_SOURCE_HISTORY"
    )

    assert (
        capture["factors"][
            "Exit Quote"
        ]["missing"]
        == 1
    )

    assert (
        capture["factors"][
            "Exit Quote"
        ]["status_counts"][
            "UNAVAILABLE"
        ]
        == 1
    )

