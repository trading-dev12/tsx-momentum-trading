"""
Northstar Headless Trading Services

Builds the complete set of headless paper-trading services.

IMPORTANT:
Importing this module does NOT start any service.
Services start only when start_headless_trading_services()
is explicitly called.
"""

from core.headless_eod import (
    start_headless_eod_service,
)
from core.headless_execution import (
    build_headless_paper_engines,
    start_headless_execution_services,
)


def start_headless_trading_services(
    engine_builder=build_headless_paper_engines,
    execution_starter=start_headless_execution_services,
    eod_starter=start_headless_eod_service,
):
    """
    Build the three paper engines and start the automatic
    execution and EOD background services exactly once.
    """

    engines = engine_builder()

    execution_threads = (
        execution_starter(
            engines,
        )
    )

    eod_thread = eod_starter(
        engines
    )

    return {
        "engines": engines,
        "execution_threads": execution_threads,
        "eod_thread": eod_thread,
    }


def get_headless_service_status(
    service_bundle,
):
    """
    Return thread health without starting or restarting
    any service.
    """

    execution_threads = (
        service_bundle[
            "execution_threads"
        ]
    )

    execution_running = all(
        thread.is_alive()
        for thread
        in execution_threads.values()
    )

    eod_running = (
        service_bundle["eod_thread"]
        .is_alive()
    )

    return {
        "execution_status": (
            "RUNNING"
            if execution_running
            else "STOPPED"
        ),
        "eod_status": (
            "RUNNING"
            if eod_running
            else "STOPPED"
        ),
    }
