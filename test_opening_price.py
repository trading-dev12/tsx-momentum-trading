import paper_trading.opening_price as opening_price


def test_opening_price_uses_ibkr_first(monkeypatch):
    monkeypatch.setattr(
        opening_price,
        "get_ibkr_open_price",
        lambda symbol, requested_date: {
            "success": True,
            "symbol": symbol,
            "trading_date": requested_date.isoformat(),
            "open_price": 66.41,
            "price_source": "IBKR_ONE_MINUTE_OPEN",
        },
    )

    def fail_if_yahoo_called(*args, **kwargs):
        raise AssertionError(
            "Yahoo should not be called when IBKR succeeds."
        )

    monkeypatch.setattr(
        opening_price,
        "get_intraday_open_price",
        fail_if_yahoo_called,
    )

    result = opening_price.get_market_open_price(
        "PAAS.TO",
        "2026-08-05",
    )

    assert result["success"] is True
    assert result["open_price"] == 66.41
    assert result["price_source"] == "IBKR_ONE_MINUTE_OPEN"


def test_opening_price_falls_back_to_yahoo_intraday(monkeypatch):
    monkeypatch.setattr(
        opening_price,
        "get_ibkr_open_price",
        lambda symbol, requested_date: {
            "success": False,
            "symbol": symbol,
            "trading_date": requested_date.isoformat(),
            "message": "IBKR unavailable",
        },
    )

    monkeypatch.setattr(
        opening_price,
        "get_intraday_open_price",
        lambda symbol, requested_date: 66.41,
    )

    def fail_if_daily_called(*args, **kwargs):
        raise AssertionError(
            "Daily Yahoo fallback should not be called "
            "when intraday Yahoo succeeds."
        )

    monkeypatch.setattr(
        opening_price,
        "get_daily_open_price",
        fail_if_daily_called,
    )

    result = opening_price.get_market_open_price(
        "PAAS.TO",
        "2026-08-05",
    )

    assert result["success"] is True
    assert result["open_price"] == 66.41
    assert result["price_source"] == "ONE_MINUTE_OPEN"


def test_opening_price_falls_back_to_yahoo_daily(monkeypatch):
    monkeypatch.setattr(
        opening_price,
        "get_ibkr_open_price",
        lambda symbol, requested_date: {
            "success": False,
            "symbol": symbol,
            "trading_date": requested_date.isoformat(),
            "message": "IBKR unavailable",
        },
    )

    monkeypatch.setattr(
        opening_price,
        "get_intraday_open_price",
        lambda symbol, requested_date: None,
    )

    monkeypatch.setattr(
        opening_price,
        "get_daily_open_price",
        lambda symbol, requested_date: 66.41,
    )

    result = opening_price.get_market_open_price(
        "PAAS.TO",
        "2026-08-05",
    )

    assert result["success"] is True
    assert result["open_price"] == 66.41
    assert result["price_source"] == "DAILY_OPEN"
def test_price_source_survives_execution_and_journal(
    tmp_path,
    monkeypatch,
):
    import csv

    import paper_trading.paper_engine as paper_engine_module
    from paper_trading.paper_engine import PaperTradingEngine

    monkeypatch.setattr(
        paper_engine_module,
        "enrich_trade",
        lambda position: {},
    )

    monkeypatch.setattr(
        PaperTradingEngine,
        "_notify_trade_opened",
        lambda self, position: None,
    )

    monkeypatch.setattr(
        PaperTradingEngine,
        "_notify_trade_closed",
        lambda self, trade: None,
    )

    journal_path = tmp_path / "journal.csv"

    engine = PaperTradingEngine(
        starting_cash=500000,
        portfolio_state_file=tmp_path / "portfolio.json",
        pending_trades_file=tmp_path / "pending.csv",
        journal_file=journal_path,
        risk_model="fixed",
        fixed_risk_amount=100,
        max_open_positions=100,
    )

    engine.queue_signal(
        {
            "symbol": "PAAS.TO",
            "strategy": "MOMENTUM",
            "decision": "READY",
            "signal_date": "2026-08-04",
            "close": 65.00,
            "atr": 2.00,
            "tmqs": 100,
            "rvol": 3.00,
            "breakout": True,
            "reason": "Price-source regression test",
        }
    )

    def fake_price_provider(symbol, trading_date):
        return {
            "success": True,
            "symbol": symbol,
            "trading_date": trading_date,
            "open_price": 66.41,
            "price_source": "IBKR_ONE_MINUTE_OPEN",
        }

    execution = engine.execute_pending_trades_for_date(
        execution_date="2026-08-05",
        price_provider=fake_price_provider,
    )

    assert execution["executed"] == 1
    assert (
        execution["results"][0]["price_source"]
        == "IBKR_ONE_MINUTE_OPEN"
    )

    assert (
        engine.portfolio.open_positions[0]["price_source"]
        == "IBKR_ONE_MINUTE_OPEN"
    )

    close_result = engine.close_position(
        symbol="PAAS.TO",
        exit_price=70.00,
        current_date="2026-08-06",
        exit_reason="Manual exit",
    )

    assert close_result["success"] is True
    assert (
        close_result["trade"]["price_source"]
        == "IBKR_ONE_MINUTE_OPEN"
    )

    with open(
        journal_path,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["price_source"] == "IBKR_ONE_MINUTE_OPEN"
    assert float(rows[0]["entry_price"]) == 66.41
