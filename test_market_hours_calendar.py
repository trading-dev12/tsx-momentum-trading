from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.market_hours import (
    get_tsx_market_status,
    is_tsx_trading_day,
)
from paper_trading.position_manager import count_trading_days


TORONTO = ZoneInfo("America/Toronto")


def test_2026_civic_holiday_is_closed():
    assert is_tsx_trading_day(date(2026, 8, 3)) is False


def test_2026_normal_weekday_is_open():
    assert is_tsx_trading_day(date(2026, 8, 4)) is True


def test_2027_new_years_day_is_closed():
    assert is_tsx_trading_day(date(2027, 1, 1)) is False


def test_2027_family_day_is_closed():
    assert is_tsx_trading_day(date(2027, 2, 15)) is False


def test_2027_good_friday_is_closed():
    assert is_tsx_trading_day(date(2027, 3, 26)) is False


def test_2027_canada_day_is_closed():
    assert is_tsx_trading_day(date(2027, 7, 1)) is False


def test_2027_civic_holiday_is_closed():
    assert is_tsx_trading_day(date(2027, 8, 2)) is False


def test_2027_thanksgiving_is_closed():
    assert is_tsx_trading_day(date(2027, 10, 11)) is False


def test_2027_christmas_observed_is_closed():
    assert is_tsx_trading_day(date(2027, 12, 27)) is False


def test_2027_boxing_day_observed_is_closed():
    assert is_tsx_trading_day(date(2027, 12, 28)) is False


def test_position_holding_counter_skips_2026_civic_holiday():
    assert count_trading_days(
        "2026-07-28",
        "2026-08-07",
    ) == 8


def test_market_status_reports_holiday_closed():
    result = get_tsx_market_status(
        datetime(
            2026,
            8,
            3,
            12,
            0,
            tzinfo=TORONTO,
        )
    )

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False


def test_2026_christmas_eve_before_early_close_is_open():
    result = get_tsx_market_status(
        datetime(
            2026,
            12,
            24,
            12,
            59,
            tzinfo=TORONTO,
        )
    )

    assert result["status"] == "OPEN"
    assert result["is_open"] is True


def test_2026_christmas_eve_at_early_close_is_closed():
    result = get_tsx_market_status(
        datetime(
            2026,
            12,
            24,
            13,
            0,
            tzinfo=TORONTO,
        )
    )

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False


def test_2026_christmas_eve_after_early_close_is_closed():
    result = get_tsx_market_status(
        datetime(
            2026,
            12,
            24,
            14,
            30,
            tzinfo=TORONTO,
        )
    )

    assert result["status"] == "CLOSED"
    assert result["is_open"] is False