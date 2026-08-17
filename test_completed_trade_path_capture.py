import csv
from datetime import datetime

from core.market_hours import (
    TORONTO_TIMEZONE,
)
from paper_trading.paper_engine import (
    PaperTradingEngine,
)


def build_engine(
    tmp_path,
):
    return PaperTradingEngine(
        starting_cash=500000,
        portfolio_state_file=(
            tmp_path / "portfolio.json"
        ),
        pending_trades_file=(
            tmp_path / "pending.csv"
        ),
        journal_file=(
            tmp_path / "journal.csv"
        ),
        risk_model="fixed",
        fixed_risk_amount=100.0,
        max_open_positions=100,
    )


def open_test_position(
    engine,
):
    result = engine.portfolio.open_position(
        {
            "symbol": "TEST.TO",
            "strategy": "MOMENTUM",
            "signal_date": "2026-08-17",
            "signal_close": 99.0,
            "signal_reason": "Research test",
            "signal_snapshot_json": "{}",
            "entry_date": "2026-08-18",
            "entry_price": 100.0,
            "price_source": (
                "IBKR_ONE_MINUTE_OPEN"
            ),
            "shares": 10,
            "stop_price": 98.0,
            "target_price": 105.0,
            "atr": 1.0,
            "tmqs": 90.0,
            "rvol": 2.0,
            "breakout": "BREAKOUT",
            "max_hold_days": 10,
            "research": {},
        }
    )

    assert result["success"] is True


def read_journal(
    tmp_path,
):
    with (
        tmp_path / "journal.csv"
    ).open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def test_closed_trade_records_timestamp_and_path_metrics(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    open_test_position(
        engine
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_closed",
        lambda trade: None,
    )

    monkeypatch.setattr(
        "paper_trading.paper_engine.capture_trade_path",
        lambda trade: {
            "trade_path_status": "COMPLETE",
            "trade_path_source": (
                "IBKR_ONE_MINUTE"
            ),
            "trade_path_bar_count": 25,
            "trade_path_bars_saved": 25,
            "highest_price": 106.0,
            "lowest_price": 99.0,
            "mfe_amount": 60.0,
            "mfe_percent": 6.0,
            "mfe_r": 3.0,
            "mfe_timestamp": (
                "2026-08-18T10:00:00-04:00"
            ),
            "mae_amount": 10.0,
            "mae_percent": 1.0,
            "mae_r": 0.5,
            "mae_timestamp": (
                "2026-08-18T09:35:00-04:00"
            ),
        },
    )

    closed = engine.update_positions(
        latest_prices={
            "TEST.TO": 106.0,
        },
        current_date="2026-08-18",
        current_datetime=datetime(
            2026,
            8,
            18,
            10,
            5,
            tzinfo=TORONTO_TIMEZONE,
        ),
    )

    assert len(closed) == 1

    trade = closed[0]

    assert (
        trade["exit_timestamp"]
        == "2026-08-18T10:05:00-04:00"
    )

    assert (
        trade["trade_path_status"]
        == "COMPLETE"
    )

    assert trade["highest_price"] == 106.0
    assert trade["lowest_price"] == 99.0
    assert trade["mfe_r"] == 3.0
    assert trade["mae_r"] == 0.5

    rows = read_journal(
        tmp_path
    )

    assert len(rows) == 1

    row = rows[0]

    assert (
        row["exit_timestamp"]
        == "2026-08-18T10:05:00-04:00"
    )

    assert (
        row["trade_path_status"]
        == "COMPLETE"
    )

    assert row["trade_path_bar_count"] == "25"
    assert row["highest_price"] == "106.0"
    assert row["lowest_price"] == "99.0"
    assert row["mfe_r"] == "3.0"
    assert row["mae_r"] == "0.5"


def test_trade_still_closes_and_journals_when_path_capture_fails(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    open_test_position(
        engine
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_closed",
        lambda trade: None,
    )

    def failed_capture(
        trade,
    ):
        raise RuntimeError(
            "Research provider unavailable"
        )

    monkeypatch.setattr(
        "paper_trading.paper_engine.capture_trade_path",
        failed_capture,
    )

    closed = engine.update_positions(
        latest_prices={
            "TEST.TO": 106.0,
        },
        current_date="2026-08-18",
        current_datetime=datetime(
            2026,
            8,
            18,
            10,
            5,
            tzinfo=TORONTO_TIMEZONE,
        ),
    )

    # Trading action still completed.
    assert len(closed) == 1
    assert (
        len(
            engine.portfolio.open_positions
        )
        == 0
    )

    trade = closed[0]

    assert (
        trade["trade_path_status"]
        == "ERROR"
    )

    assert (
        "Research provider unavailable"
        in trade["trade_path_error"]
    )

    # Journal still survives the research failure.
    rows = read_journal(
        tmp_path
    )

    assert len(rows) == 1

    assert (
        rows[0]["trade_path_status"]
        == "ERROR"
    )

    assert (
        "Research provider unavailable"
        in rows[0]["trade_path_error"]
    )


def test_manual_close_also_records_exit_timestamp(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    open_test_position(
        engine
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_closed",
        lambda trade: None,
    )

    monkeypatch.setattr(
        "paper_trading.paper_engine.capture_trade_path",
        lambda trade: {
            "trade_path_status": "NO_DATA",
            "trade_path_source": (
                "IBKR_ONE_MINUTE"
            ),
            "trade_path_bar_count": 0,
            "trade_path_bars_saved": 0,
        },
    )

    result = engine.close_position(
        symbol="TEST.TO",
        exit_price=101.0,
        current_date="2026-08-18",
        exit_reason="Manual exit",
        current_datetime=datetime(
            2026,
            8,
            18,
            11,
            15,
            tzinfo=TORONTO_TIMEZONE,
        ),
    )

    assert result["success"] is True

    trade = result["trade"]

    assert (
        trade["exit_timestamp"]
        == "2026-08-18T11:15:00-04:00"
    )

    assert (
        trade["trade_path_status"]
        == "NO_DATA"
    )
