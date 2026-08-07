from datetime import datetime

from core.market_hours import TORONTO_TIMEZONE
from paper_trading.eod_recovery import (
    get_previous_tsx_trading_day,
    get_recoverable_eod_datetime,
)


def test_previous_trading_day_skips_weekend():
    result = get_previous_tsx_trading_day(
        datetime(
            2026,
            8,
            10,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        )
    )

    assert result.isoformat() == "2026-08-07"


def test_missed_friday_eod_recoverable_on_saturday():
    result = get_recoverable_eod_datetime(
        current_datetime=datetime(
            2026,
            8,
            8,
            10,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        last_run_date="2026-08-06",
    )

    assert result is not None
    assert result.date().isoformat() == "2026-08-07"
    assert result.hour == 16
    assert result.minute == 5


def test_missed_friday_eod_recoverable_monday_premarket():
    result = get_recoverable_eod_datetime(
        current_datetime=datetime(
            2026,
            8,
            10,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        last_run_date="2026-08-06",
    )

    assert result is not None
    assert result.date().isoformat() == "2026-08-07"
    assert result.hour == 16
    assert result.minute == 5


def test_missed_eod_not_recovered_after_next_market_open():
    result = get_recoverable_eod_datetime(
        current_datetime=datetime(
            2026,
            8,
            10,
            9,
            30,
            tzinfo=TORONTO_TIMEZONE,
        ),
        last_run_date="2026-08-06",
    )

    assert result is None


def test_completed_eod_is_not_recovered_again():
    result = get_recoverable_eod_datetime(
        current_datetime=datetime(
            2026,
            8,
            10,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        last_run_date="2026-08-07",
    )

    assert result is None


def test_same_day_after_eod_time_left_to_normal_scheduler():
    result = get_recoverable_eod_datetime(
        current_datetime=datetime(
            2026,
            8,
            7,
            16,
            30,
            tzinfo=TORONTO_TIMEZONE,
        ),
        last_run_date="2026-08-06",
    )

    assert result is None