from pathlib import Path

import pytest

from analytics.strategy_analytics import StrategyAnalytics


def write_journal(path: Path, profit_losses):
    rows = ["symbol,profit_loss"]

    for index, profit_loss in enumerate(profit_losses, start=1):
        rows.append(f"TEST{index}.TO,{profit_loss}")

    path.write_text(
        "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def test_strategy_analytics_summary(tmp_path):
    journal = tmp_path / "journal.csv"
    write_journal(journal, [100, -50, 0])

    analytics = StrategyAnalytics(
        "Momentum",
        journal,
    )
    summary = analytics.summary()

    assert summary["strategy"] == "Momentum"
    assert summary["total_trades"] == 3
    assert summary["winning_trades"] == 1
    assert summary["losing_trades"] == 1
    assert summary["win_rate"] == pytest.approx(33.333333)
    assert summary["realized_pl"] == pytest.approx(50.0)
    assert summary["average_win"] == pytest.approx(100.0)
    assert summary["average_loss"] == pytest.approx(-50.0)
    assert summary["largest_win"] == pytest.approx(100.0)
    assert summary["largest_loss"] == pytest.approx(-50.0)
    assert summary["profit_factor"] == pytest.approx(2.0)
    assert summary["expectancy"] == pytest.approx(16.666667)


def test_strategy_analytics_empty_journal(tmp_path):
    journal = tmp_path / "missing.csv"

    analytics = StrategyAnalytics(
        "Mean Reversion",
        journal,
    )
    summary = analytics.summary()

    assert summary["total_trades"] == 0
    assert summary["winning_trades"] == 0
    assert summary["losing_trades"] == 0
    assert summary["win_rate"] == 0.0
    assert summary["realized_pl"] == 0.0
    assert summary["average_win"] == 0.0
    assert summary["average_loss"] == 0.0
    assert summary["largest_win"] == 0.0
    assert summary["largest_loss"] == 0.0
    assert summary["profit_factor"] == 0.0
    assert summary["expectancy"] == 0.0
