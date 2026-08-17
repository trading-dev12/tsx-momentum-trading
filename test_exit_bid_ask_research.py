import csv

import core.market_data as market_data

from paper_trading.paper_engine import (
    PaperTradingEngine,
)


def build_engine(tmp_path):
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


def queue_signal(engine):
    result = engine.queue_signal(
        {
            "symbol": "TEST.TO",
            "strategy": "MOMENTUM",
            "decision": "READY",
            "signal_date": "2026-08-17",
            "close": 100.0,
            "atr": 1.0,
            "tmqs": 90.0,
            "rvol": 2.0,
            "breakout": True,
            "reason": "Exit spread research",
        }
    )

    assert result["success"] is True


def prepare_engine(
    engine,
    monkeypatch,
):
    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_opened",
        lambda position: None,
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


def test_live_quote_preserves_ibkr_bid_and_ask(
    monkeypatch,
):
    monkeypatch.setattr(
        market_data,
        "get_previous_day",
        lambda symbol: {
            "previous_close": 99.0,
            "previous_high": 101.0,
            "previous_low": 98.0,
        },
    )

    monkeypatch.setattr(
        market_data,
        "get_average_volume",
        lambda symbol: 1000.0,
    )

    monkeypatch.setattr(
        market_data,
        "calculate_live_atr",
        lambda symbol: 1.0,
    )

    monkeypatch.setattr(
        market_data,
        "get_52_week_breakout_metrics",
        lambda symbol: {
            "prior_52_week_high": 110.0,
            "sma_50": 100.0,
            "sma_200": 90.0,
        },
    )

    monkeypatch.setattr(
        market_data,
        "get_mean_reversion_metrics",
        lambda symbol: {
            "sma_20": 100.0,
            "rsi_2": 50.0,
            "rsi_14": 50.0,
            "bollinger_lower": 95.0,
        },
    )

    monkeypatch.setattr(
        market_data,
        "calculate_score",
        lambda quote: 0,
    )

    monkeypatch.setattr(
        market_data,
        "grade_stock",
        lambda quote: {},
    )

    monkeypatch.setattr(
        market_data,
        "calculate_tmqs",
        lambda quote: 0,
    )

    monkeypatch.setattr(
        market_data,
        "get_breakout_status",
        lambda quote: "INSIDE RANGE",
    )

    monkeypatch.setattr(
        market_data,
        "calculate_confidence_score",
        lambda quote: 0,
    )

    monkeypatch.setattr(
        market_data,
        "get_trade_decision",
        lambda quote: (
            "IGNORE",
            "Research test",
        ),
    )

    monkeypatch.setattr(
        market_data,
        "build_breakout_52week_input",
        lambda quote: {},
    )

    class FakeDecision:
        value = "IGNORE"

    class FakeResult:
        decision = FakeDecision()
        reason = "Research test"
        breakout = False

    class FakeStrategy:
        def evaluate(self, data):
            return FakeResult()

    monkeypatch.setattr(
        market_data,
        "Breakout52WeekStrategy",
        FakeStrategy,
    )

    quote = market_data.get_live_quote(
        "TEST.TO",
        live_quote={
            "symbol": "TEST.TO",
            "price": 100.0,
            "price_source": "LAST",
            "last": 100.0,
            "bid": 99.95,
            "ask": 100.05,
            "volume": 500.0,
            "source": "IBKR",
        },
    )

    assert quote is not None
    assert quote["data_source"] == "IBKR"
    assert quote["last"] == 100.0
    assert quote["bid"] == 99.95
    assert quote["ask"] == 100.05
    assert quote["quote_timestamp"]


def test_automatic_exit_snapshot_saved_to_journal(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    queue_signal(engine)

    prepare_engine(
        engine,
        monkeypatch,
    )

    opened = engine.execute_pending_trade(
        symbol="TEST.TO",
        entry_price=100.0,
        entry_date="2026-08-18",
    )

    assert opened["success"] is True

    closed = engine.update_positions(
        latest_prices={
            "TEST.TO": 105.0,
        },
        current_date="2026-08-18",
        market_snapshots={
            "TEST.TO": {
                "symbol": "TEST.TO",
                "price": 105.0,
                "last": 105.0,
                "bid": 104.95,
                "ask": 105.05,
                "data_source": "IBKR",
                "quote_timestamp": (
                    "2026-08-18T10:15:00-04:00"
                ),
            }
        },
    )

    assert len(closed) == 1

    trade = closed[0]

    assert (
        trade["exit_quote_status"]
        == "AVAILABLE"
    )

    assert trade["exit_quote_source"] == "IBKR"
    assert trade["exit_bid"] == 104.95
    assert trade["exit_ask"] == 105.05
    assert trade["exit_midpoint"] == 105.0

    assert (
        trade["exit_spread_amount"]
        == 0.1
    )

    with (
        tmp_path / "journal.csv"
    ).open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1

    row = rows[0]

    assert (
        row["exit_quote_status"]
        == "AVAILABLE"
    )

    assert row["exit_quote_source"] == "IBKR"
    assert row["exit_bid"] == "104.95"
    assert row["exit_ask"] == "105.05"


def test_yahoo_manual_exit_records_unavailable_and_still_closes(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    queue_signal(engine)

    prepare_engine(
        engine,
        monkeypatch,
    )

    opened = engine.execute_pending_trade(
        symbol="TEST.TO",
        entry_price=100.0,
        entry_date="2026-08-18",
    )

    assert opened["success"] is True

    result = engine.close_position(
        symbol="TEST.TO",
        exit_price=101.0,
        current_date="2026-08-18",
        market_snapshot={
            "symbol": "TEST.TO",
            "price": 101.0,
            "data_source": (
                "YAHOO_FALLBACK"
            ),
            "quote_timestamp": (
                "2026-08-18T11:00:00-04:00"
            ),
        },
    )

    assert result["success"] is True

    trade = result["trade"]

    assert (
        trade["exit_quote_status"]
        == "UNAVAILABLE"
    )

    assert (
        trade["exit_quote_source"]
        == "YAHOO_FALLBACK"
    )

    assert trade["exit_last"] == 101.0

    assert len(
        engine.portfolio.open_positions
    ) == 0


def test_exit_snapshot_failure_cannot_block_trade_close(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    queue_signal(engine)

    prepare_engine(
        engine,
        monkeypatch,
    )

    opened = engine.execute_pending_trade(
        symbol="TEST.TO",
        entry_price=100.0,
        entry_date="2026-08-18",
    )

    assert opened["success"] is True

    def fail_snapshot(*args, **kwargs):
        raise RuntimeError(
            "Research snapshot failure"
        )

    monkeypatch.setattr(
        "paper_trading.paper_engine.build_market_snapshot",
        fail_snapshot,
    )

    result = engine.close_position(
        symbol="TEST.TO",
        exit_price=101.0,
        current_date="2026-08-18",
        market_snapshot={
            "symbol": "TEST.TO",
            "price": 101.0,
            "bid": 100.95,
            "ask": 101.05,
            "data_source": "IBKR",
        },
    )

    assert result["success"] is True

    trade = result["trade"]

    assert (
        trade["exit_quote_status"]
        == "ERROR"
    )

    assert (
        "Research snapshot failure"
        in trade["exit_quote_error"]
    )

    assert len(
        engine.portfolio.open_positions
    ) == 0
