"""
Safe tests for Northstar headless position monitoring.

All quote retrieval and paper engines are mocked.
No live market data or real portfolio state is touched.
"""

from unittest.mock import MagicMock

from core.headless_position_monitor import (
    build_current_prices,
    collect_open_position_symbols,
    run_headless_position_monitor_cycle,
)


def make_engine(symbols):
    engine = MagicMock()

    engine.portfolio.open_positions = [
        {"symbol": symbol}
        for symbol in symbols
    ]

    return engine


def test_collect_open_position_symbols():
    engines = {
        "momentum": make_engine(
            ["RY.TO", "SU.TO"]
        ),
        "52_week_breakout": make_engine(
            ["SU.TO", "CNQ.TO"]
        ),
        "mean_reversion": make_engine(
            ["BMO.TO"]
        ),
    }

    symbols = collect_open_position_symbols(
        engines
    )

    assert symbols == [
        "BMO.TO",
        "CNQ.TO",
        "RY.TO",
        "SU.TO",
    ]


def test_build_current_prices():
    quotes = [
        {
            "symbol": "RY.TO",
            "price": 201.25,
        },
        {
            "symbol": "SU.TO",
            "close": 71.50,
        },
    ]

    prices = build_current_prices(
        quotes
    )

    assert prices == {
        "RY.TO": 201.25,
        "SU.TO": 71.50,
    }


def test_no_open_positions_skips_quote_provider():
    engines = {
        "momentum": make_engine([]),
        "52_week_breakout": make_engine([]),
        "mean_reversion": make_engine([]),
    }

    quote_provider = MagicMock()

    result = run_headless_position_monitor_cycle(
        engines,
        quote_provider=quote_provider,
        current_date="2026-08-08",
    )

    assert result == {
        "status": "NO_OPEN_POSITIONS",
        "symbols": [],
        "prices": {},
        "closed_trades": {},
        "closed_total": 0,
    }

    quote_provider.assert_not_called()

    for engine in engines.values():
        engine.update_positions.assert_not_called()


def test_position_monitor_updates_all_engines():
    momentum = make_engine(
        ["RY.TO"]
    )

    breakout = make_engine(
        ["SU.TO"]
    )

    mean_reversion = make_engine(
        ["BMO.TO"]
    )

    momentum.update_positions.return_value = [
        {"symbol": "RY.TO"}
    ]

    breakout.update_positions.return_value = []

    mean_reversion.update_positions.return_value = [
        {"symbol": "BMO.TO"}
    ]

    engines = {
        "momentum": momentum,
        "52_week_breakout": breakout,
        "mean_reversion": mean_reversion,
    }

    quote_provider = MagicMock(
        return_value=[
            {
                "symbol": "RY.TO",
                "price": 201.25,
            },
            {
                "symbol": "SU.TO",
                "price": 71.50,
            },
            {
                "symbol": "BMO.TO",
                "price": 189.10,
            },
        ]
    )

    result = run_headless_position_monitor_cycle(
        engines,
        quote_provider=quote_provider,
        current_date="2026-08-08",
    )

    expected_prices = {
        "RY.TO": 201.25,
        "SU.TO": 71.50,
        "BMO.TO": 189.10,
    }

    quote_provider.assert_called_once_with(
        [
            "BMO.TO",
            "RY.TO",
            "SU.TO",
        ]
    )

    for engine in engines.values():
        engine.update_positions.assert_called_once_with(
            latest_prices=expected_prices,
            current_date="2026-08-08",
        )

    assert result["status"] == "COMPLETED"
    assert result["prices"] == expected_prices
    assert result["closed_total"] == 2

    assert result["closed_trades"] == {
        "momentum": [
            {"symbol": "RY.TO"}
        ],
        "52_week_breakout": [],
        "mean_reversion": [
            {"symbol": "BMO.TO"}
        ],
    }
