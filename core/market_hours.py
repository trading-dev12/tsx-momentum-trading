"""
TSX Market Hours

Determines whether the Toronto Stock Exchange is:
- PRE_MARKET
- OPEN
- CLOSED

Times are evaluated in the Toronto time zone.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo


TORONTO_TIMEZONE = ZoneInfo("America/Toronto")

MARKET_OPEN_TIME = time(9, 30)
MARKET_CLOSE_TIME = time(16, 0)


def get_tsx_market_status(current_datetime=None):
    """
    Return the current TSX market status.

    This first version handles:
    - Monday through Friday
    - Pre-market before 9:30 AM
    - Open market from 9:30 AM through 4:00 PM
    - Closed market after 4:00 PM
    - Weekends

    Exchange holidays will be added separately.
    """
    if current_datetime is None:
        current_datetime = datetime.now(TORONTO_TIMEZONE)
    elif current_datetime.tzinfo is None:
        current_datetime = current_datetime.replace(tzinfo=TORONTO_TIMEZONE)
    else:
        current_datetime = current_datetime.astimezone(TORONTO_TIMEZONE)

    weekday = current_datetime.weekday()
    current_time = current_datetime.time().replace(tzinfo=None)

    if weekday >= 5:
        return {
            "status": "CLOSED",
            "is_open": False,
            "can_open_trade": False,
            "message": "Weekend - Next Open: Monday 9:30 AM ET",
            "current_time": current_datetime,
        }

    if current_time < MARKET_OPEN_TIME:
        hours = MARKET_OPEN_TIME.hour - current_time.hour
        minutes = MARKET_OPEN_TIME.minute - current_time.minute

        if minutes < 0:
            hours -= 1
            minutes += 60

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
        return {
            "status": "CLOSED",
            "is_open": False,
            "can_open_trade": False,
            "message": "Market closed - Next Open: 9:30 AM ET",
            "current_time": current_datetime,
        }
    return {
        "status": "OPEN",
        "is_open": True,
        "can_open_trade": True,
        "message": "TSX regular trading session is open.",
        "current_time": current_datetime,
    }