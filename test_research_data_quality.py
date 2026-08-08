import csv

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
