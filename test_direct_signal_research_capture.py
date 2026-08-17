import json

from paper_trading.paper_engine import (
    PaperTradingEngine,
)


def test_direct_signal_preserves_research_snapshot(
    tmp_path,
    monkeypatch,
):
    engine = PaperTradingEngine(
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

    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_opened",
        lambda position: None,
    )

    signal = {
        "symbol": "TEST.TO",
        "strategy": "MOMENTUM",
        "decision": "READY",
        "signal_date": "2026-08-18",
        "date": "2026-08-18",
        "price": 101.0,
        "close": 100.0,
        "atr": 1.25,
        "tmqs": 88.0,
        "rvol": 2.1,
        "breakout": "BREAKOUT",
        "reason": "Research snapshot test",
        "data_source": "IBKR",
        "price_source": "LAST",
        "bid": 100.95,
        "ask": 101.05,
        "stop_price": 98.5,
        "target_price": 107.25,
    }

    result = engine.process_signal(
        signal
    )

    assert result["success"] is True

    position = (
        engine.portfolio.open_positions[0]
    )

    assert position["signal_date"] == "2026-08-18"
    assert position["signal_close"] == 100.0

    assert (
        position["signal_reason"]
        == "Research snapshot test"
    )

    assert position["atr"] == 1.25
    assert position["breakout"] == "BREAKOUT"
    assert position["price_source"] == "LAST"

    snapshot = json.loads(
        position["signal_snapshot_json"]
    )

    assert snapshot["symbol"] == "TEST.TO"
    assert snapshot["tmqs"] == 88.0
    assert snapshot["rvol"] == 2.1
    assert snapshot["bid"] == 100.95
    assert snapshot["ask"] == 101.05

    assert (
        position["entry_quote_status"]
        == "AVAILABLE"
    )
