"""
Northstar missed EOD recovery helpers.

Determines whether the most recent missed TSX end-of-day
workflow can still be safely recovered before the next
regular trading session begins.
"""

from datetime import date, datetime, timedelta

from core.market_hours import (
    MARKET_OPEN_TIME,
    TORONTO_TIMEZONE,
    get_tsx_market_close_time,
    is_tsx_trading_day,
    normalize_tsx_datetime,
)


EOD_DELAY_MINUTES = 5


def get_previous_tsx_trading_day(
    start_date,
):
    """
    Return the most recent TSX trading day before start_date.
    """

    if isinstance(
        start_date,
        datetime,
    ):
        start_date = normalize_tsx_datetime(
            start_date
        ).date()

    if not isinstance(
        start_date,
        date,
    ):
        raise TypeError(
            "start_date must be a date or datetime."
        )

    candidate = (
        start_date
        - timedelta(days=1)
    )

    while not is_tsx_trading_day(
        candidate
    ):
        candidate -= timedelta(days=1)

    return candidate


def get_recoverable_eod_datetime(
    current_datetime=None,
    last_run_date=None,
):
    """
    Return the synthetic EOD datetime that should be recovered.

    Recovery is permitted only when the latest missed trading
    day's signals are still valid for the next market open.

    The normal same-day EOD scheduler remains responsible for
    scans after today's close.
    """

    now = normalize_tsx_datetime(
        current_datetime
    )

    today = now.date()

    current_time = (
        now.time().replace(
            tzinfo=None
        )
    )

    if is_tsx_trading_day(today):
        market_close = (
            get_tsx_market_close_time(
                today
            )
        )

        same_day_due = now.replace(
            hour=market_close.hour,
            minute=market_close.minute,
            second=0,
            microsecond=0,
        ) + timedelta(
            minutes=EOD_DELAY_MINUTES
        )

        if now >= same_day_due:
            return None

        if current_time >= MARKET_OPEN_TIME:
            return None

    target_date = (
        get_previous_tsx_trading_day(
            today
        )
    )

    if last_run_date:
        try:
            completed_date = (
                date.fromisoformat(
                    last_run_date
                )
            )

        except ValueError:
            completed_date = None

        if (
            completed_date is not None
            and completed_date >= target_date
        ):
            return None

    market_close = (
        get_tsx_market_close_time(
            target_date
        )
    )

    return datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        market_close.hour,
        market_close.minute,
        tzinfo=TORONTO_TIMEZONE,
    ) + timedelta(
        minutes=EOD_DELAY_MINUTES
    )