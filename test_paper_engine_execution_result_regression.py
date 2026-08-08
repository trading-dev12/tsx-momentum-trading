from types import SimpleNamespace

from paper_trading.paper_engine import PaperTradingEngine


class FakePendingTrades:
    def __init__(self, trades):
        self.trades = list(trades)
        self.removed = []

    def get_all(self):
        return list(self.trades)

    def remove_trade(self, symbol):
        self.removed.append(symbol)


def build_engine(pending_trades):
    engine = PaperTradingEngine.__new__(
        PaperTradingEngine
    )

    engine.pending_trades = FakePendingTrades(
        pending_trades
    )

    engine.portfolio = SimpleNamespace(
        open_positions=[]
    )

    return engine


def test_execution_cycle_handles_empty_pending_queue():
    engine = build_engine([])

    result = (
        engine.execute_pending_trades_for_date(
            execution_date="2026-08-07",
            price_provider=lambda symbol, date: {
                "success": True,
                "open_price": 100.0,
            },
        )
    )

    assert result == {
        "execution_date": "2026-08-07",
        "attempted": 0,
        "executed": 0,
        "price_unavailable": 0,
        "skipped": 0,
        "failed": 0,
        "results": [],
    }


def test_execution_cycle_handles_only_skipped_trades():
    engine = build_engine(
        [
            {
                "symbol": "TEST.TO",
                "signal_date": "2026-08-07",
            }
        ]
    )

    result = (
        engine.execute_pending_trades_for_date(
            execution_date="2026-08-07",
            price_provider=lambda symbol, date: {
                "success": True,
                "open_price": 100.0,
            },
        )
    )

    assert result["attempted"] == 1
    assert result["executed"] == 0
    assert result["skipped"] == 1
    assert result["failed"] == 0

    assert len(result["results"]) == 1

    assert (
        result["results"][0]["status"]
        == "SKIPPED"
    )


def test_execution_cycle_appends_each_executed_trade():
    engine = build_engine(
        [
            {
                "symbol": "AAA.TO",
                "signal_date": "2026-08-06",
            },
            {
                "symbol": "BBB.TO",
                "signal_date": "2026-08-06",
            },
        ]
    )

    def fake_price_provider(
        symbol,
        execution_date,
    ):
        prices = {
            "AAA.TO": 100.0,
            "BBB.TO": 200.0,
        }

        return {
            "success": True,
            "open_price": prices[symbol],
            "price_source": "TEST",
        }

    def fake_execute_pending_trade(**kwargs):
        return {
            "success": True,
            "message": (
                f"{kwargs['symbol']} executed."
            ),
        }

    engine.execute_pending_trade = (
        fake_execute_pending_trade
    )

    result = (
        engine.execute_pending_trades_for_date(
            execution_date="2026-08-07",
            price_provider=fake_price_provider,
        )
    )

    assert result["attempted"] == 2
    assert result["executed"] == 2
    assert result["price_unavailable"] == 0
    assert result["skipped"] == 0
    assert result["failed"] == 0

    assert len(result["results"]) == 2

    assert [
        trade["symbol"]
        for trade in result["results"]
    ] == [
        "AAA.TO",
        "BBB.TO",
    ]

    assert all(
        trade["status"] == "EXECUTED"
        for trade in result["results"]
    )