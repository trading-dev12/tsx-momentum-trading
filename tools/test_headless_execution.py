"""
Safe tests for Northstar headless automatic execution.

All paper engines and execution workers are mocked.
No real trades, queues, journals, or portfolio files are touched.
"""

from unittest.mock import MagicMock, call, patch

import core.headless_execution as headless_execution


def test_build_headless_paper_engines():
    fake_momentum = MagicMock(name="momentum_engine")
    fake_breakout = MagicMock(name="breakout_engine")
    fake_mean_reversion = MagicMock(
        name="mean_reversion_engine"
    )

    with patch.object(
        headless_execution,
        "PaperTradingEngine",
        side_effect=[
            fake_momentum,
            fake_breakout,
            fake_mean_reversion,
        ],
    ) as engine_class:
        engines = (
            headless_execution
            .build_headless_paper_engines()
        )

    assert engines == {
        "momentum": fake_momentum,
        "52_week_breakout": fake_breakout,
        "mean_reversion": fake_mean_reversion,
    }

    assert engine_class.call_count == 3

    assert engine_class.call_args_list == [
        call(
            starting_cash=500000,
            risk_model="fixed",
            fixed_risk_amount=100.0,
            max_open_positions=100,
        ),
        call(
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
        ),
        call(
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
        ),
    ]


def test_start_headless_execution_services():
    engines = {
        "momentum": MagicMock(name="momentum"),
        "52_week_breakout": MagicMock(
            name="breakout"
        ),
        "mean_reversion": MagicMock(
            name="mean_reversion"
        ),
    }

    fake_threads = [
        MagicMock(name="momentum_thread"),
        MagicMock(name="breakout_thread"),
        MagicMock(name="mean_reversion_thread"),
    ]

    with patch.object(
        headless_execution,
        "start_automatic_execution_service",
        side_effect=fake_threads,
    ) as start_service:
        threads = (
            headless_execution
            .start_headless_execution_services(
                engines
            )
        )

    assert start_service.call_args_list == [
        call(engines["momentum"]),
        call(engines["52_week_breakout"]),
        call(engines["mean_reversion"]),
    ]

    assert threads == {
        "momentum": fake_threads[0],
        "52_week_breakout": fake_threads[1],
        "mean_reversion": fake_threads[2],
    }
