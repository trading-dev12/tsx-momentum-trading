"""
Northstar Headless Automatic Execution

Creates the same three paper-trading engines used by the GUI
and provides a helper for starting their automatic execution
workers.

IMPORTANT:
This module has no startup side effects.
Importing it does NOT execute trades or start workers.
"""

from paper_trading.automatic_execution import (
    start_automatic_execution_service,
)
from paper_trading.paper_engine import (
    PaperTradingEngine,
)


def build_headless_paper_engines():
    momentum_engine = PaperTradingEngine(
        starting_cash=500000,
        risk_model="fixed",
        fixed_risk_amount=100.0,
        max_open_positions=100,
    )

    breakout_52week_engine = PaperTradingEngine(
        starting_cash=500000,
        portfolio_state_file=(
            "paper_portfolio_state_52week.json"
        ),
        pending_trades_file=(
            "pending_trades_52week.csv"
        ),
        journal_file=(
            "paper_trade_journal_52week.csv"
        ),
        risk_model="fixed",
        fixed_risk_amount=100.0,
        max_open_positions=100,
    )

    mean_reversion_engine = PaperTradingEngine(
        starting_cash=500000,
        portfolio_state_file=(
            "paper_portfolio_state_mean_reversion.json"
        ),
        pending_trades_file=(
            "pending_trades_mean_reversion.csv"
        ),
        journal_file=(
            "paper_trade_journal_mean_reversion.csv"
        ),
        risk_model="fixed",
        fixed_risk_amount=100.0,
        max_open_positions=100,
    )

    return {
        "momentum": momentum_engine,
        "52_week_breakout": breakout_52week_engine,
        "mean_reversion": mean_reversion_engine,
    }


def start_headless_execution_services(
    engines,
):
    return {
        "momentum": (
            start_automatic_execution_service(
                engines["momentum"],
            )
        ),
        "52_week_breakout": (
            start_automatic_execution_service(
                engines["52_week_breakout"],
            )
        ),
        "mean_reversion": (
            start_automatic_execution_service(
                engines["mean_reversion"],
            )
        ),
    }
