from datetime import date, timedelta

import pytest

from research import relative_strength
from research.market_regime import calculate_market_regime


def _weekday_dates(end_date, count):
    dates = []
    current = end_date

    while len(dates) < count:
        if current.weekday() < 5:
            dates.append(current)
        current -= timedelta(days=1)

    return list(reversed(dates))


def _write_history_csv(path, end_date, count=220, symbol="XIC.TO"):
    dates = _weekday_dates(end_date, count)

    lines = [
        "Price,Adj Close,Close",
        f"Ticker,{symbol},{symbol}",
        "Date,,",
    ]

    for index, trading_date in enumerate(dates):
        close = 50.0 + (index * 0.05)
        lines.append(
            f"{trading_date.isoformat()},{close},{close}"
        )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def test_relative_strength_rejects_stale_local_fallback(
    tmp_path,
    monkeypatch,
):
    history_file = tmp_path / "XIC_TO.csv"

    _write_history_csv(
        history_file,
        date(2026, 7, 17),
    )

    monkeypatch.setattr(
        relative_strength,
        "historical_file_path",
        lambda symbol: history_file,
    )

    with pytest.raises(
        ValueError,
        match="stale",
    ):
        relative_strength.load_adjusted_close_history(
            "XIC.TO",
            "2026-08-10",
        )


def test_relative_strength_allows_previous_friday_for_weekend(
    tmp_path,
    monkeypatch,
):
    history_file = tmp_path / "XIC_TO.csv"

    _write_history_csv(
        history_file,
        date(2026, 7, 17),
    )

    monkeypatch.setattr(
        relative_strength,
        "historical_file_path",
        lambda symbol: history_file,
    )

    prices = (
        relative_strength.load_adjusted_close_history(
            "XIC.TO",
            "2026-07-19",
        )
    )

    assert prices.index[-1].date() == date(
        2026,
        7,
        17,
    )


def test_market_regime_rejects_stale_local_fallback(
    tmp_path,
):
    history_file = tmp_path / "XIC_TO.csv"

    _write_history_csv(
        history_file,
        date(2026, 7, 17),
    )

    result = calculate_market_regime(
        "2026-08-10",
        benchmark_file=history_file,
    )

    assert result["status"] == "UNAVAILABLE"
    assert result["data_source"] == "UNAVAILABLE"
    assert "stale" in result["reason"].lower()


def test_market_regime_allows_previous_friday_for_weekend(
    tmp_path,
):
    history_file = tmp_path / "XIC_TO.csv"

    _write_history_csv(
        history_file,
        date(2026, 7, 17),
    )

    result = calculate_market_regime(
        "2026-07-19",
        benchmark_file=history_file,
    )

    assert result["status"] == "AVAILABLE"
    assert result[
        "data_source"
    ] == "LOCAL_BENCHMARK_FILE"


def test_relative_strength_allows_previous_trading_day_for_tsx_holiday(
    tmp_path,
    monkeypatch,
):
    history_file = tmp_path / "XIC_TO.csv"

    # Friday July 31 precedes the Monday Aug 3 TSX holiday.
    _write_history_csv(
        history_file,
        date(2026, 7, 31),
    )

    monkeypatch.setattr(
        relative_strength,
        "historical_file_path",
        lambda symbol: history_file,
    )

    prices = (
        relative_strength.load_adjusted_close_history(
            "XIC.TO",
            "2026-08-03",
        )
    )

    assert prices.index[-1].date() == date(
        2026,
        7,
        31,
    )


def test_market_regime_allows_previous_trading_day_for_tsx_holiday(
    tmp_path,
):
    history_file = tmp_path / "XIC_TO.csv"

    _write_history_csv(
        history_file,
        date(2026, 7, 31),
    )

    result = calculate_market_regime(
        "2026-08-03",
        benchmark_file=history_file,
    )

    assert result["status"] == "AVAILABLE"
    assert result[
        "data_source"
    ] == "LOCAL_BENCHMARK_FILE"
