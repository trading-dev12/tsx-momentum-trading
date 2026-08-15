from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from core.market_hours import (
    get_next_tsx_trading_day,
    get_tsx_holidays,
    get_tsx_market_close_time,
    get_tsx_market_status,
    is_tsx_trading_day,
)


TORONTO = ZoneInfo("America/Toronto")


def test_recurring_holiday_generator_handles_future_year():
    holidays = get_tsx_holidays(2027)

    expected = {
        date(2027, 1, 1),   # New Year's Day
        date(2027, 2, 15),  # Family Day
        date(2027, 3, 26),  # Good Friday
        date(2027, 5, 24),  # Victoria Day
        date(2027, 7, 1),   # Canada Day
        date(2027, 8, 2),   # Civic Holiday
        date(2027, 9, 6),   # Labour Day
        date(2027, 10, 11), # Thanksgiving
        date(2027, 12, 27), # Christmas observed
        date(2027, 12, 28), # Boxing Day observed
    }

    assert expected.issubset(holidays)


def test_weekend_is_not_trading_day():
    assert is_tsx_trading_day(date(2026, 8, 15)) is False


def test_future_year_holiday_is_not_trading_day():
    assert is_tsx_trading_day(date(2027, 7, 1)) is False


def test_regular_weekday_is_trading_day():
    assert is_tsx_trading_day(date(2027, 7, 2)) is True


def test_next_trading_day_skips_christmas_closures():
    assert get_next_tsx_trading_day(
        date(2026, 12, 24)
    ) == date(2026, 12, 29)


def test_regular_market_close_is_4pm():
    assert get_tsx_market_close_time(
        date(2026, 8, 14)
    ) == time(16, 0)


def test_christmas_eve_2026_closes_at_1pm():
    assert get_tsx_market_close_time(
        date(2026, 12, 24)
    ) == time(13, 0)


def test_regular_day_pre_market_status():
    result = get_tsx_market_status(
        datetime(2026, 8, 14, 8, 30, tzinfo=TORONTO)
    )

    assert result["status"] == "PRE-MARKET"
    assert result["is_open"] is False
    assert result["can_open_trade"] is False


def test_regular_day_market_open_status():
    result = get_tsx_market_status(
        datetime(2026, 8, 14, 10, 0, tzinfo=TORONTO)
    )

    assert result["status"] == "OPEN"
    assert result["is_open"] is True
    assert result["can_open_trade"] is True


def test_regular_day_market_closed_at_4pm():
    result = get_tsx_market_status(
        datetime(2026, 8, 14, 16, 0, tzinfo=TORONTO)
    )

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False
    assert result["can_open_trade"] is False


def test_early_close_day_open_before_1pm():
    result = get_tsx_market_status(
        datetime(2026, 12, 24, 12, 59, tzinfo=TORONTO)
    )

    assert result["status"] == "OPEN"
    assert result["is_open"] is True


def test_early_close_day_closed_at_1pm():
    result = get_tsx_market_status(
        datetime(2026, 12, 24, 13, 0, tzinfo=TORONTO)
    )

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False
    assert result["can_open_trade"] is False
