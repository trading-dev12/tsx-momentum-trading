"""
Northstar Headless Automatic EOD

Provides the headless equivalent of the workstation's
automatic EOD service.

IMPORTANT:
Importing this module does NOT start the EOD worker.
"""

from paper_trading.automatic_eod import (
    start_automatic_eod_service,
)


def start_headless_eod_service(engines):
    """
    Start automatic EOD using the three headless paper engines.

    The normal EOD scanner is self-contained and does not
    require a GUI snapshot. A headless live-snapshot fallback
    can be added later when the headless scanner is ready.
    """

    return start_automatic_eod_service(
        engines["momentum"],
        breakout_52week_engine=(
            engines["52_week_breakout"]
        ),
        mean_reversion_engine=(
            engines["mean_reversion"]
        ),
        live_snapshot_provider=None,
    )
