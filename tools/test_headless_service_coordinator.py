"""
Safe tests for the Northstar headless service coordinator.

All market status, scanner, position-monitoring, and engine
objects are mocked. No live market data or portfolio state is
touched.
"""

from unittest.mock import MagicMock

from core.headless_service_coordinator import (
    run_headless_market_cycle,
)


def test_market_closed_skips_market_services():
    engines = {
        "momentum": MagicMock(),
        "52_week_breakout": MagicMock(),
        "mean_reversion": MagicMock(),
    }

    market_status_provider = MagicMock(
        return_value={
            "is_open": False,
            "message": "TSX market is closed.",
        }
    )

    scanner_cycle = MagicMock()
    position_cycle = MagicMock()

    result = run_headless_market_cycle(
        engines=engines,
        refresh_id=12,
        market_status_provider=(
            market_status_provider
        ),
        scanner_cycle=scanner_cycle,
        position_cycle=position_cycle,
    )

    market_status_provider.assert_called_once_with()
    scanner_cycle.assert_not_called()
    position_cycle.assert_not_called()

    assert result["status"] == "MARKET_CLOSED"
    assert result["refresh_id"] == 12
    assert result["scanner"] is None
    assert result["positions"] is None


def test_market_open_runs_scanner_and_positions():
    engines = {
        "momentum": MagicMock(),
        "52_week_breakout": MagicMock(),
        "mean_reversion": MagicMock(),
    }

    market_status = {
        "is_open": True,
        "message": "TSX market is open.",
    }

    market_status_provider = MagicMock(
        return_value=market_status
    )

    scanner_result = {
        "status": "COMPLETED",
        "refresh_id": 13,
    }

    position_result = {
        "status": "COMPLETED",
        "closed_total": 0,
    }

    scanner_cycle = MagicMock(
        return_value=scanner_result
    )

    position_cycle = MagicMock(
        return_value=position_result
    )

    result = run_headless_market_cycle(
        engines=engines,
        refresh_id=13,
        market_status_provider=(
            market_status_provider
        ),
        scanner_cycle=scanner_cycle,
        position_cycle=position_cycle,
    )

    market_status_provider.assert_called_once_with()

    scanner_cycle.assert_called_once_with(
        refresh_id=13,
    )

    position_cycle.assert_called_once_with(
        engines,
    )

    assert result == {
        "status": "COMPLETED",
        "refresh_id": 13,
        "market_status": market_status,
        "scanner": scanner_result,
        "positions": position_result,
    }
