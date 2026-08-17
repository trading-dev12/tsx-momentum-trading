from paper_trading import opening_price
from paper_trading.paper_engine import (
    PaperTradingEngine,
)
from research.market_snapshot import (
    build_market_snapshot,
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
            "reason": "Entry spread research",
        }
    )

    assert result["success"] is True


def test_market_snapshot_calculates_spread():
    result = build_market_snapshot(
        "entry",
        {
            "data_source": "IBKR",
            "bid": 99.90,
            "ask": 100.10,
            "last": 100.00,
            "quote_timestamp": (
                "2026-08-18T09:30:05-04:00"
            ),
        },
    )

    assert (
        result["entry_quote_status"]
        == "AVAILABLE"
    )
    assert result["entry_midpoint"] == 100.0
    assert result["entry_spread_amount"] == 0.2
    assert result["entry_spread_percent"] == 0.2


def test_ibkr_open_survives_snapshot_failure(
    monkeypatch,
):
    class FakeProvider:
        def __init__(self, client_id):
            self.disconnected = False

        def get_market_open_price(
            self,
            symbol,
            requested_date,
        ):
            return {
                "success": True,
                "symbol": symbol,
                "trading_date": (
                    requested_date.isoformat()
                ),
                "open_price": 100.0,
                "price_source": (
                    "IBKR_ONE_MINUTE_OPEN"
                ),
            }

        def get_quote(self, symbol):
            raise RuntimeError(
                "Snapshot unavailable"
            )

        def disconnect(self):
            self.disconnected = True

    monkeypatch.setattr(
        opening_price,
        "IBKRDataProvider",
        FakeProvider,
    )

    result = opening_price.get_ibkr_open_price(
        "TEST.TO",
        opening_price.normalize_date(
            "2026-08-18"
        ),
    )

    assert result["success"] is True
    assert result["open_price"] == 100.0

    assert (
        result["entry_quote_status"]
        == "UNAVAILABLE"
    )

    assert (
        "Snapshot unavailable"
        in result["entry_quote_error"]
    )


def test_ibkr_snapshot_reaches_open_position(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )
    queue_signal(engine)

    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )
    monkeypatch.setattr(
        engine,
        "_notify_trade_opened",
        lambda position: None,
    )

    result = engine.execute_pending_trades_for_date(
        execution_date="2026-08-18",
        price_provider=lambda symbol, date: {
            "success": True,
            "symbol": symbol,
            "trading_date": date,
            "open_price": 100.0,
            "price_source": (
                "IBKR_ONE_MINUTE_OPEN"
            ),
            "entry_quote_status": (
                "AVAILABLE"
            ),
            "entry_quote_source": "IBKR",
            "entry_quote_timestamp": (
                "2026-08-18T09:30:05-04:00"
            ),
            "entry_bid": 99.95,
            "entry_ask": 100.05,
            "entry_last": 100.0,
            "entry_midpoint": 100.0,
            "entry_spread_amount": 0.10,
            "entry_spread_percent": 0.10,
            "entry_quote_error": "",
        },
    )

    assert result["executed"] == 1

    position = (
        engine.portfolio.open_positions[0]
    )

    assert (
        position["entry_quote_status"]
        == "AVAILABLE"
    )
    assert position["entry_bid"] == 99.95
    assert position["entry_ask"] == 100.05
    assert position["entry_midpoint"] == 100.0
    assert position["entry_spread_percent"] == 0.10


def test_yahoo_entry_is_recorded_as_unavailable(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )
    queue_signal(engine)

    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )
    monkeypatch.setattr(
        engine,
        "_notify_trade_opened",
        lambda position: None,
    )

    result = engine.execute_pending_trades_for_date(
        execution_date="2026-08-18",
        price_provider=lambda symbol, date: {
            "success": True,
            "symbol": symbol,
            "trading_date": date,
            "open_price": 100.0,
            "price_source": (
                "ONE_MINUTE_OPEN"
            ),
        },
    )

    assert result["executed"] == 1

    position = (
        engine.portfolio.open_positions[0]
    )

    assert (
        position["entry_quote_status"]
        == "UNAVAILABLE"
    )
    assert (
        position["entry_quote_source"]
        == "ONE_MINUTE_OPEN"
    )
