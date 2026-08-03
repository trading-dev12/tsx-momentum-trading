"""
TSX Market Hours

Provides the shared source of truth for:
- TSX trading days
- Exchange holidays
- Regular market hours
- PRE-MARKET, OPEN, and CLOSED status

Times are evaluated in the Toronto time zone.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


TORONTO_TIMEZONE = ZoneInfo("America/Toronto")

MARKET_OPEN_TIME = time(9, 30)
MARKET_CLOSE_TIME = time(16, 0)


TSX_HOLIDAYS = {
    2026: {
        date(2026, 1, 1),    # New Year's Day
        date(2026, 2, 16),   # Family Day
        date(2026, 4, 3),    # Good Friday
        date(2026, 5, 18),   # Victoria Day
        date(2026, 7, 1),    # Canada Day
        date(2026, 8, 3),    # Civic Holiday
        date(2026, 9, 7),    # Labour Day
        date(2026, 10, 12),  # Thanksgiving Day
        date(2026, 12, 25),  # Christmas Day
        date(2026, 12, 28),  # Boxing Day observed
    },
}


def normalize_tsx_datetime(current_datetime=None):
    """
    Return a timezone-aware datetime in Toronto time.
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


def is_tsx_trading_day(trading_date):
    """
    Return True when the supplied date is a regular TSX
    trading day.

    Weekends and configured exchange holidays return False.
    """

    if isinstance(trading_date, datetime):
        trading_date = normalize_tsx_datetime(
            trading_date
        ).date()

    if not isinstance(trading_date, date):
        raise TypeError(
            "trading_date must be a date or datetime."
        )

    if trading_date.weekday() >= 5:
        return False

    holidays = TSX_HOLIDAYS.get(
        trading_date.year,
        set(),
    )

    return trading_date not in holidays


def get_next_tsx_trading_day(start_date):
    """
    Return the first TSX trading day after start_date.
    """

    if isinstance(start_date, datetime):
        start_date = normalize_tsx_datetime(
            start_date
        ).date()

    candidate = start_date + timedelta(days=1)

    while not is_tsx_trading_day(candidate):
        candidate += timedelta(days=1)

    return candidate


def get_tsx_market_status(current_datetime=None):
    """
    Return the current TSX market status.
    """

    current_datetime = normalize_tsx_datetime(
        current_datetime
    )

    current_date = current_datetime.date()
    current_time = (
        current_datetime.time().replace(tzinfo=None)
    )

    if not is_tsx_trading_day(current_date):
        next_open_date = get_next_tsx_trading_day(
            current_date
        )

        return {
            "status": "CLOSED",
            "is_open": False,
            "can_open_trade": False,
            "message": (
                "TSX closed today. Next open: "
                f"{next_open_date.strftime('%A, %B %d')} "
                "at 9:30 AM ET"
            ),
            "current_time": current_datetime,
            "next_open_date": next_open_date,
        }

    if current_time < MARKET_OPEN_TIME:
        market_open = current_datetime.replace(
            hour=MARKET_OPEN_TIME.hour,
            minute=MARKET_OPEN_TIME.minute,
            second=0,
            microsecond=0,
        )

        time_until_open = market_open - current_datetime
        total_minutes = max(
            0,
            int(time_until_open.total_seconds() // 60),
        )

        hours, minutes = divmod(
            total_minutes,
            60,
        )

        return {
            "status": "PRE-MARKET",
            "is_open": False,
            "can_open_trade": False,
            "message": (
                f"Market opens in {hours}h {minutes}m "
                "(9:30 AM ET)"
            ),
            "current_time": current_datetime,
        }

    if current_time >= MARKET_CLOSE_TIME:
        next_open_date = get_next_tsx_trading_day(
            current_date
        )

        return {
            "status": "CLOSED",
            "is_open": False,
            "can_open_trade": False,
            "message": (
                "Market closed. Next open: "
                f"{next_open_date.strftime('%A, %B %d')} "
                "at 9:30 AM ET"
            ),
            "current_time": current_datetime,
            "next_open_date": next_open_date,
        }

    return {
        "status": "OPEN",
        "is_open": True,
        "can_open_trade": True,
        "message": (
            "TSX regular trading session is open."
        ),
        "current_time": current_datetime,
    }