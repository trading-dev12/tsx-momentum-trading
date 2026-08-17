import csv
import json

from paper_trading.journal import save_trade
from paper_trading.paper_engine import PaperTradingEngine
from paper_trading.pending_trades import PendingTradeQueue


def build_signal():
    return {
        "symbol": "TEST.TO",
        "strategy": "MEAN_REVERSION",
        "decision": "READY",
        "signal_date": "2026-08-17",
        "close": 10.0,
        "atr": 1.0,
        "tmqs": 88.0,
        "rvol": 1.7,
        "breakout": "NO_BREAKOUT",
        "reason": "Research test signal",
        "rsi_2": 4.25,
        "rsi_14": 37.5,
        "sma_20": 11.2,
        "bollinger_lower": 10.4,
        "price_vs_sma20_percent": -10.7143,
        "price_vs_lower_band_percent": -3.8462,
    }


def test_pending_queue_preserves_complete_signal_snapshot(tmp_path):
    pending_file = tmp_path / "pending.csv"

    queue = PendingTradeQueue(
        file_path=pending_file
    )

    result = queue.add_trade(
        build_signal()
    )

    assert result["success"] is True

    saved = queue.get_trade(
        "TEST.TO"
    )

    snapshot = json.loads(
        saved["signal_snapshot_json"]
    )

    assert snapshot["strategy"] == "MEAN_REVERSION"
    assert snapshot["rsi_2"] == 4.25
    assert snapshot["bollinger_lower"] == 10.4
    assert snapshot["price_vs_sma20_percent"] == -10.7143

    reloaded = PendingTradeQueue(
        file_path=pending_file
    )

    persisted = reloaded.get_trade(
        "TEST.TO"
    )

    persisted_snapshot = json.loads(
        persisted["signal_snapshot_json"]
    )

    assert persisted_snapshot == snapshot


def test_signal_snapshot_survives_into_open_position(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )

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
        engine,
        "_notify_trade_opened",
        lambda position: None,
    )

    engine.queue_signal(
        build_signal()
    )

    result = engine.execute_pending_trade(
        symbol="TEST.TO",
        entry_price=10.5,
        entry_date="2026-08-18",
    )

    assert result["success"] is True

    position = (
        engine.portfolio.open_positions[0]
    )

    assert position["signal_date"] == "2026-08-17"
    assert position["signal_close"] == 10.0
    assert (
        position["signal_reason"]
        == "Research test signal"
    )

    snapshot = json.loads(
        position["signal_snapshot_json"]
    )

    assert snapshot["rsi_2"] == 4.25
    assert snapshot["rsi_14"] == 37.5


def test_completed_journal_preserves_signal_snapshot(
    tmp_path,
):
    journal_file = (
        tmp_path / "journal.csv"
    )

    signal = build_signal()

    trade = {
        "symbol": "TEST.TO",
        "strategy": "MEAN_REVERSION",
        "signal_date": signal["signal_date"],
        "signal_close": signal["close"],
        "signal_reason": signal["reason"],
        "signal_snapshot_json": json.dumps(
            signal,
            sort_keys=True,
        ),
        "entry_date": "2026-08-18",
        "exit_date": "2026-08-20",
        "entry_price": 10.5,
        "exit_price": 11.0,
        "shares": 50,
        "stop_price": 8.5,
        "target_price": 15.5,
        "exit_reason": "Time exit",
        "profit_loss": 25.0,
        "profit_loss_percent": 4.7619,
        "research": {},
    }

    save_trade(
        trade,
        file_path=journal_file,
    )

    with journal_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1
    assert rows[0]["signal_date"] == "2026-08-17"
    assert rows[0]["signal_close"] == "10.0"
    assert (
        rows[0]["signal_reason"]
        == "Research test signal"
    )

    snapshot = json.loads(
        rows[0]["signal_snapshot_json"]
    )

    assert snapshot["rsi_2"] == 4.25
    assert snapshot["bollinger_lower"] == 10.4
