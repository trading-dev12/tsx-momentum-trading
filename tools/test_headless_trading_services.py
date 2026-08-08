"""
Safe tests for Northstar headless trading services.

All paper engines and service starters are mocked.
No execution worker, EOD worker, market-data request,
or portfolio modification occurs.
"""

from unittest.mock import MagicMock

from core.headless_trading_services import (
    get_headless_service_status,
    start_headless_trading_services,
)


def make_thread(is_alive):
    thread = MagicMock()
    thread.is_alive.return_value = is_alive
    return thread


def test_start_headless_trading_services():
    engines = {
        "momentum": MagicMock(),
        "52_week_breakout": MagicMock(),
        "mean_reversion": MagicMock(),
    }

    execution_threads = {
        "momentum": make_thread(True),
        "52_week_breakout": make_thread(True),
        "mean_reversion": make_thread(True),
    }

    eod_thread = make_thread(True)

    engine_builder = MagicMock(
        return_value=engines
    )

    execution_starter = MagicMock(
        return_value=execution_threads
    )

    eod_starter = MagicMock(
        return_value=eod_thread
    )

    result = start_headless_trading_services(
        engine_builder=engine_builder,
        execution_starter=execution_starter,
        eod_starter=eod_starter,
    )

    engine_builder.assert_called_once_with()

    execution_starter.assert_called_once_with(
        engines
    )

    eod_starter.assert_called_once_with(
        engines
    )

    assert result == {
        "engines": engines,
        "execution_threads": execution_threads,
        "eod_thread": eod_thread,
    }


def test_service_status_running():
    service_bundle = {
        "execution_threads": {
            "momentum": make_thread(True),
            "52_week_breakout": make_thread(True),
            "mean_reversion": make_thread(True),
        },
        "eod_thread": make_thread(True),
    }

    status = get_headless_service_status(
        service_bundle
    )

    assert status == {
        "execution_status": "RUNNING",
        "eod_status": "RUNNING",
    }


def test_service_status_detects_stopped_worker():
    service_bundle = {
        "execution_threads": {
            "momentum": make_thread(True),
            "52_week_breakout": make_thread(False),
            "mean_reversion": make_thread(True),
        },
        "eod_thread": make_thread(False),
    }

    status = get_headless_service_status(
        service_bundle
    )

    assert status == {
        "execution_status": "STOPPED",
        "eod_status": "STOPPED",
    }
