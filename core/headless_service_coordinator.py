"""
Northstar Headless Service Coordinator

Coordinates one headless market-data cycle.

IMPORTANT:
Importing this module does NOT start any services,
scan the market, or modify portfolio state.
"""

from core.headless_position_monitor import (
    run_headless_position_monitor_cycle,
)
from core.headless_scanner import (
    run_headless_scanner_cycle,
)
from core.market_hours import (
    get_tsx_market_status,
)


def run_headless_market_cycle(
    engines,
    refresh_id,
    market_status_provider=get_tsx_market_status,
    scanner_cycle=run_headless_scanner_cycle,
    position_cycle=run_headless_position_monitor_cycle,
):
    """
    Run one scanner and position-monitor cycle only while
    the TSX market is open.
    """

    market_status = market_status_provider()

    if not market_status.get(
        "is_open",
        False,
    ):
        return {
            "status": "MARKET_CLOSED",
            "refresh_id": refresh_id,
            "market_status": market_status,
            "scanner": None,
            "positions": None,
        }

    scanner_result = scanner_cycle(
        refresh_id=refresh_id,
    )

    position_result = position_cycle(
        engines,
    )

    return {
        "status": "COMPLETED",
        "refresh_id": refresh_id,
        "market_status": market_status,
        "scanner": scanner_result,
        "positions": position_result,
    }
