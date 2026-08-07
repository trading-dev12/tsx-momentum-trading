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

TSX_EARLY_CLOSES = {
    date(2026, 12, 24): time(13, 0),
}

def _nth_weekday_of_month(year, month, weekday, occurrence):
    first_day = date(year, month, 1)

    days_until_weekday = (
        weekday - first_day.weekday()
    ) % 7

    return first_day + timedelta(
        days=days_until_weekday + (occurrence - 1) * 7
    )


def _victoria_day(year):
    candidate = date(year, 5, 24)

    while candidate.weekday() != 0:
        candidate -= timedelta(days=1)

    return candidate


def _easter_sunday(year):
    """
    Return Gregorian Easter Sunday.
    """

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (
        19 * a
        + b
        - d
        - g
        + 15
    ) % 30
    i = c // 4
    k = c % 4
    l = (
        32
        + 2 * e
        + 2 * i
        - h
        - k
    ) % 7
    m = (
        a
        + 11 * h
        + 22 * l
    ) // 451

    month = (
        h
        + l
        - 7 * m
        + 114
    ) // 31

    day = (
        (
            h
            + l
            - 7 * m
            + 114
        ) % 31
    ) + 1

    return date(year, month, day)


def _observed_weekday(holiday):
    if holiday.weekday() == 5:
        return holiday + timedelta(days=2)

    if holiday.weekday() == 6:
        return holiday + timedelta(days=1)

    return holiday
def get_tsx_holidays(year):
    """
    Return the recurring full-day TSX closures
    for the supplied calendar year.

    TMX-published schedules remain the authority
    for exceptional closures or schedule changes.
    """

    holidays = set()

    # New Year's Day
    holidays.add(
        _observed_weekday(
            date(year, 1, 1)
        )
    )

    # Family Day - third Monday in February
    holidays.add(
        _nth_weekday_of_month(
            year,
            2,
            0,
            3,
        )
    )

    # Good Friday
    holidays.add(
        _easter_sunday(year)
        - timedelta(days=2)
    )

    # Victoria Day - Monday preceding May 25
    holidays.add(
        _victoria_day(year)
    )

    # Canada Day
    holidays.add(
        _observed_weekday(
            date(year, 7, 1)
        )
    )

    # Civic Holiday - first Monday in August
    holidays.add(
        _nth_weekday_of_month(
            year,
            8,
            0,
            1,
        )
    )

    # Labour Day - first Monday in September
    holidays.add(
        _nth_weekday_of_month(
            year,
            9,
            0,
            1,
        )
    )

    # Thanksgiving - second Monday in October
    holidays.add(
        _nth_weekday_of_month(
            year,
            10,
            0,
            2,
        )
    )

    # Christmas and Boxing Day
    christmas = date(year, 12, 25)
    boxing_day = date(year, 12, 26)

    if christmas.weekday() == 5:
        # Christmas Saturday, Boxing Day Sunday:
        # observed Monday and Tuesday.
        holidays.add(
            christmas + timedelta(days=2)
        )
        holidays.add(
            boxing_day + timedelta(days=2)
        )

    elif christmas.weekday() == 6:
        # Christmas Sunday, Boxing Day Monday:
        # Boxing Day Monday, Christmas observed Tuesday.
        holidays.add(boxing_day)
        holidays.add(
            christmas + timedelta(days=2)
        )

    else:
        holidays.add(christmas)

        if boxing_day.weekday() == 5:
            holidays.add(
                boxing_day + timedelta(days=2)
            )

        elif boxing_day.weekday() == 6:
            holidays.add(
                boxing_day + timedelta(days=1)
            )

        else:
            holidays.add(boxing_day)

    return holidays

def get_tsx_market_close_time(trading_date):
    """
    Return the regular or explicitly configured
    TSX closing time for the supplied date.
    """

    if isinstance(
        trading_date,
        datetime,
    ):
        trading_date = normalize_tsx_datetime(
            trading_date
        ).date()

    if not isinstance(
        trading_date,
        date,
    ):
        raise TypeError(
            "trading_date must be a date or datetime."
        )

    return TSX_EARLY_CLOSES.get(
        trading_date,
        MARKET_CLOSE_TIME,
    )

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

    holidays = get_tsx_holidays(
        trading_date.year
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
        current_datetime.time().replace(
            tzinfo=None
        )
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

        time_until_open = (
            market_open
            - current_datetime
        )

        total_minutes = max(
            0,
            int(
                time_until_open.total_seconds()
                // 60
            ),
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

    market_close_time = get_tsx_market_close_time(
        current_date
    )

    if current_time >= market_close_time:
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