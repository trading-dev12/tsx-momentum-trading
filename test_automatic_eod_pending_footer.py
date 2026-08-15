from paper_trading.automatic_eod import (
    build_pending_execution_footer,
    get_pending_trade_count,
)


class FakePendingTrades:
    def __init__(self, trades):
        self.trades = trades

    def get_all(self):
        return list(self.trades)


class FakeEngine:
    def __init__(self, trades):
        self.pending_trades = FakePendingTrades(
            trades
        )


def test_pending_count_uses_actual_engine_queue():
    engine = FakeEngine(
        [
            {"symbol": "AAA.TO"},
            {"symbol": "BBB.TO"},
        ]
    )

    assert get_pending_trade_count(
        engine,
        fallback=99,
    ) == 2


def test_pending_count_supports_lightweight_test_double():
    class LightweightEngine:
        pass

    assert get_pending_trade_count(
        LightweightEngine(),
        fallback=3,
    ) == 3


def test_pending_footer_reports_zero_accurately():
    assert build_pending_execution_footer(0) == (
        "No pending signals awaiting "
        "next-day execution."
    )


def test_pending_footer_uses_singular_wording():
    assert build_pending_execution_footer(1) == (
        "1 pending signal is ready for "
        "next-day execution."
    )


def test_pending_footer_uses_plural_wording():
    assert build_pending_execution_footer(4) == (
        "4 pending signals are ready "
        "for next-day execution."
    )
