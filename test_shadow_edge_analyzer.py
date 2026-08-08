import csv

from research.shadow_edge_analyzer import (
    analyze_journal,
    calculate_baseline_stats,
    compare_categorical_factor,
)


def test_calculate_baseline_stats():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "2.0",
        },
        {
            "profit_loss": "-50",
            "profit_loss_percent": "-1.0",
        },
        {
            "profit_loss": "25",
            "profit_loss_percent": "0.5",
        },
        {
            "profit_loss": "-25",
            "profit_loss_percent": "-0.5",
        },
    ]

    result = calculate_baseline_stats(
        trades
    )

    assert result["trade_count"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 2
    assert result["breakeven"] == 0
    assert result["win_rate"] == 50.0
    assert result["gross_profit"] == 125.0
    assert result["gross_loss"] == 75.0

    assert round(
        result["profit_factor"],
        4,
    ) == 1.6667

    assert result["total_profit_loss"] == 50.0
    assert result["expectancy"] == 12.5
    assert result["average_gain"] == 62.5
    assert result["average_loss"] == 37.5
    assert result["average_return_percent"] == 0.25
    assert result["sample_status"] == "VERY_EARLY"


def test_analyze_journal_reads_csv(tmp_path):
    journal = (
        tmp_path / "journal.csv"
    )

    with journal.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "symbol",
                "profit_loss",
                "profit_loss_percent",
            ],
        )

        writer.writeheader()

        writer.writerow(
            {
                "symbol": "ABC.TO",
                "profit_loss": "100",
                "profit_loss_percent": "1.5",
            }
        )

        writer.writerow(
            {
                "symbol": "XYZ.TO",
                "profit_loss": "-50",
                "profit_loss_percent": "-0.75",
            }
        )

    result = analyze_journal(
        journal
    )

    assert result["trade_count"] == 2
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["profit_factor"] == 2.0
    assert result["expectancy"] == 25.0


def test_factor_analysis_excludes_missing_data():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-50",
            "profit_loss_percent": "-1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "20",
            "profit_loss_percent": "0.2",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "-40",
            "profit_loss_percent": "-0.4",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "1000",
            "profit_loss_percent": "10",
            "market_regime": "",
        },
    ]

    result = compare_categorical_factor(
        trades,
        "market_regime",
    )

    assert result["total_trade_count"] == 5
    assert result["eligible_trade_count"] == 4
    assert result["missing_trade_count"] == 1

    assert result[
        "eligible_baseline"
    ]["trade_count"] == 4


def test_small_factor_groups_cannot_be_promising():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-25",
            "profit_loss_percent": "-0.25",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "10",
            "profit_loss_percent": "0.1",
            "market_regime": "BEAR",
        },
    ]

    result = compare_categorical_factor(
        trades,
        "market_regime",
        minimum_sample_size=30,
    )

    statuses = {
        group["status"]
        for group in result["groups"]
    }

    assert statuses == {
        "INSUFFICIENT_DATA"
    }
