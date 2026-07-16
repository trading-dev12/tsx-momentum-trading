"""
Safe visual test for the paper-trading dashboard.

Uses isolated temporary files and never touches the live
portfolio, pending queue, journal, or Telegram notifications.
"""

from pathlib import Path

from paper_trading.dashboard import display_paper_dashboard
from paper_trading.paper_engine import PaperTradingEngine


PORTFOLIO_FILE = "test_dashboard_portfolio.json"
PENDING_FILE = "test_dashboard_pending.csv"


def cleanup_test_files():
    for filename in (
        PORTFOLIO_FILE,
        PENDING_FILE,
    ):
        path = Path(filename)

        if path.exists():
            path.unlink()


cleanup_test_files()

try:
    engine = PaperTradingEngine(
        starting_cash=10000,
        portfolio_state_file=PORTFOLIO_FILE,
        pending_trades_file=PENDING_FILE,
        risk_model="fixed",
        fixed_risk_amount=100,
        max_open_positions=10,
    )

    # Visual tests must never send Telegram messages.
    engine._notify_trade_opened = lambda position: None
    engine._notify_trade_closed = lambda trade: None

    signal = {
        "symbol": "HIVE.TO",
        "price": 5.00,
        "decision": "READY",
        "date": "2026-07-15",
        "stop_price": 4.75,
        "target_price": 5.625,
        "tmqs": 100,
        "rvol": 3.0,
        "reason": "Dashboard visual test",
    }

    result = engine.process_signal(signal)

    if not result or not result.get("success"):
        raise RuntimeError(
            f"Test position failed to open: {result}"
        )

    display_paper_dashboard(
        engine,
        {
            "HIVE.TO": 5.35,
        },
    )

finally:
    cleanup_test_files()