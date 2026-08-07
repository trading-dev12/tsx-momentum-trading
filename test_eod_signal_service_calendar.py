from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.eod_signal_service import is_daily_candle_complete


TORONTO = ZoneInfo("America/Toronto")


def test_normal_day_candle_incomplete_before_400():
    assert is_daily_candle_complete(
        date(2026, 7, 10),
        datetime(
            2026,
            7,
            10,
            15,
            59,
            tzinfo=TORONTO,
        ),
    ) is False


def test_normal_day_candle_complete_at_400():
    assert is_daily_candle_complete(
        date(2026, 7, 10),
        datetime(
            2026,
            7,
            10,
            16,
            0,
            tzinfo=TORONTO,
        ),
    ) is True


def test_early_close_candle_incomplete_before_100():
    assert is_daily_candle_complete(
        date(2026, 12, 24),
        datetime(
            2026,
            12,
            24,
            12,
            59,
            tzinfo=TORONTO,
        ),
    ) is False


def test_early_close_candle_complete_at_100():
    assert is_daily_candle_complete(
        date(2026, 12, 24),
        datetime(
            2026,
            12,
            24,
            13,
            0,
            tzinfo=TORONTO,
        ),
    ) is True


def test_holiday_candle_never_complete_as_today():
    assert is_daily_candle_complete(
        date(2026, 12, 25),
        datetime(
            2026,
            12,
            25,
            16,
            30,
            tzinfo=TORONTO,
        ),
    ) is False