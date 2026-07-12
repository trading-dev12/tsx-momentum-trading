"""
Morning Market Recorder Service

Controls the scheduled Morning Market Recorder window.

This service is research-only. It does not modify pending trades,
open positions, execution decisions, or the baseline paper-trading
workflow.
"""

from datetime import datetime, time

from core.market_hours import TORONTO_TIMEZONE


MORNING_RECORDING_START_TIME = time(9, 30)
MORNING_RECORDING_END_TIME = time(10, 0)

DEFAULT_CHECK_SECONDS = 60


def normalize_current_datetime(current_datetime=None):
    """
    Return a timezone-aware Toronto datetime.
    """

    if current_datetime is None:
        return datetime.now(TORONTO_TIMEZONE)

    if current_datetime.tzinfo is None:
        return current_datetime.replace(
            tzinfo=TORONTO_TIMEZONE,
        )

    return current_datetime.astimezone(
        TORONTO_TIMEZONE,
    )
def capture_morning_candidates(
    paper_engine,
):
    """
    Return an independent snapshot of the pending candidates.

    The returned dictionaries are copies so later queue changes
    do not alter the recorder's morning candidate list.
    """

    pending_trades = (
        paper_engine.pending_trades.get_all()
    )

    return [
        dict(pending_trade)
        for pending_trade in pending_trades
    ]

def should_record_morning_observations(
    current_datetime=None,
):
    """
    Return True during the weekday morning recording window.

    The recording window includes 9:30 a.m. and 10:00 a.m.
    Toronto time.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    if current_datetime.weekday() >= 5:
        return False

    current_time = (
        current_datetime.time().replace(tzinfo=None)
    )

    return (
        MORNING_RECORDING_START_TIME
        <= current_time
        <= MORNING_RECORDING_END_TIME
    )