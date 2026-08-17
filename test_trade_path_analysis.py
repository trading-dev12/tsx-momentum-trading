from datetime import datetime
from types import SimpleNamespace

import pytest

from core.market_hours import (
    TORONTO_TIMEZONE,
)
from paper_trading.morning_database import (
    get_trade_minute_bars,
)
from research.trade_path_analysis import (
    calculate_trade_path_metrics,
    capture_trade_path,
    normalize_trade_bars,
)


def make_bar(
    day,
    hour,
    minute,
    open_price,
    high,
    low,
    close,
    volume=100,
):
    return SimpleNamespace(
        date=datetime(
            2026,
            8,
            day,
            hour,
            minute,
            tzinfo=TORONTO_TIMEZONE,
        ),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def make_trade():
    return {
        "symbol": "TEST.TO",
        "strategy": "MOMENTUM",
        "signal_date": "2026-08-17",
        "entry_date": "2026-08-18",
        "entry_price": 100.0,
        "shares": 10,
        "stop_price": 98.0,
        "target_price": 105.0,
        "exit_date": "2026-08-18",
        "exit_timestamp": (
            "2026-08-18T09:33:30-04:00"
        ),
    }


def test_normalize_trade_bars_excludes_after_exit():
    trade = make_trade()

    bars = normalize_trade_bars(
        trade,
        [
            make_bar(
                18, 9, 29,
                99.0, 99.5, 98.5, 99.0,
            ),
            make_bar(
                18, 9, 30,
                100.0, 101.0, 99.5, 100.5,
            ),
            make_bar(
                18, 9, 31,
                100.5, 103.0, 100.0, 102.5,
            ),
            make_bar(
                18, 9, 32,
                102.5, 102.7, 97.0, 98.5,
            ),
            make_bar(
                18, 9, 34,
                98.5, 110.0, 98.0, 109.0,
            ),
        ],
    )

    assert len(bars) == 3

    assert (
        bars[0]["bar_time"]
        == "09:30:00"
    )

    assert (
        bars[-1]["bar_time"]
        == "09:32:00"
    )


def test_calculate_trade_path_metrics_uses_intraday_high_low():
    trade = make_trade()

    bars = normalize_trade_bars(
        trade,
        [
            make_bar(
                18, 9, 30,
                100.0, 101.0, 99.5, 100.5,
            ),
            make_bar(
                18, 9, 31,
                100.5, 103.0, 100.0, 102.5,
            ),
            make_bar(
                18, 9, 32,
                102.5, 102.7, 97.0, 98.5,
            ),
        ],
    )

    metrics = calculate_trade_path_metrics(
        trade,
        bars,
    )

    assert (
        metrics["trade_path_status"]
        == "COMPLETE"
    )

    assert metrics["highest_price"] == 103.0
    assert metrics["lowest_price"] == 97.0

    # $3 favourable move x 10 shares.
    assert metrics["mfe_amount"] == 30.0
    assert metrics["mfe_percent"] == 3.0
    assert metrics["mfe_r"] == 1.5

    # $3 adverse move x 10 shares.
    assert metrics["mae_amount"] == 30.0
    assert metrics["mae_percent"] == 3.0
    assert metrics["mae_r"] == 1.5

    assert "09:31:00" in (
        metrics["mfe_timestamp"]
    )

    assert "09:32:00" in (
        metrics["mae_timestamp"]
    )


class FakeProvider:
    def __init__(self, bars):
        self.bars = bars
        self.disconnected = False

    def get_historical_bars(
        self,
        symbol,
        duration,
        bar_size,
        use_rth,
        what_to_show,
    ):
        assert symbol == "TEST.TO"
        assert duration == "3 W"
        assert bar_size == "1 min"
        assert use_rth is True
        assert what_to_show == "TRADES"

        return self.bars

    def disconnect(self):
        self.disconnected = True


def test_capture_trade_path_persists_raw_minute_bars(
    tmp_path,
):
    trade = make_trade()

    provider = FakeProvider(
        [
            make_bar(
                18, 9, 30,
                100.0, 101.0, 99.5, 100.5,
            ),
            make_bar(
                18, 9, 31,
                100.5, 103.0, 100.0, 102.5,
            ),
        ]
    )

    database_file = (
        tmp_path
        / "research.db"
    )

    result = capture_trade_path(
        trade,
        provider=provider,
        database_file=database_file,
    )

    assert (
        result["trade_path_status"]
        == "COMPLETE"
    )

    assert result["trade_path_bar_count"] == 2
    assert result["trade_path_bars_saved"] == 2

    saved = get_trade_minute_bars(
        strategy="MOMENTUM",
        symbol="TEST.TO",
        entry_date="2026-08-18",
        database_file=database_file,
    )

    assert len(saved) == 2
    assert saved[0]["open_price"] == 100.0
    assert saved[1]["high_price"] == 103.0
    assert (
        saved[0]["data_source"]
        == "IBKR_ONE_MINUTE"
    )

    # Re-running is safe because the table is idempotent.
    second = capture_trade_path(
        trade,
        provider=provider,
        database_file=database_file,
    )

    assert second["trade_path_bars_saved"] == 0

    saved_again = get_trade_minute_bars(
        strategy="MOMENTUM",
        symbol="TEST.TO",
        entry_date="2026-08-18",
        database_file=database_file,
    )

    assert len(saved_again) == 2
