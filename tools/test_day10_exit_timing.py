from datetime import datetime

from core.market_hours import (
    TORONTO_TIMEZONE,
)
from paper_trading.position_manager import (
    check_exit,
)


def position():
    return {
        "symbol": "TEST.TO",
        "entry_date": "2026-08-10",
        "entry_price": 100.0,
        "stop_price": 90.0,
        "target_price": 110.0,
        "max_hold_days": 10,
    }


def ts(hour, minute):
    return datetime(
        2026,
        8,
        21,
        hour,
        minute,
        tzinfo=TORONTO_TIMEZONE,
    )


def test_day10_morning_does_not_time_exit():
    result = check_exit(
        position(),
        100.0,
        "2026-08-21",
        current_datetime=ts(9, 35),
    )

    assert result["exit"] is False


def test_day10_1559_does_not_time_exit():
    result = check_exit(
        position(),
        100.0,
        "2026-08-21",
        current_datetime=ts(15, 59),
    )

    assert result["exit"] is False


def test_day10_market_close_time_exits():
    result = check_exit(
        position(),
        100.0,
        "2026-08-21",
        current_datetime=ts(16, 0),
    )

    assert result["exit"] is True
    assert result["exit_reason"] == "Time exit"


def test_day10_stop_still_has_priority():
    result = check_exit(
        position(),
        89.0,
        "2026-08-21",
        current_datetime=ts(11, 47),
    )

    assert result["exit"] is True
    assert result["exit_reason"] == "Stop hit"
    assert result["exit_price"] == 90.0


def test_day10_target_still_has_priority():
    result = check_exit(
        position(),
        111.0,
        "2026-08-21",
        current_datetime=ts(13, 15),
    )

    assert result["exit"] is True
    assert result["exit_reason"] == "Target hit"
    assert result["exit_price"] == 110.0


def test_overdue_position_exits_next_morning():
    next_day = datetime(
        2026,
        8,
        24,
        9,
        35,
        tzinfo=TORONTO_TIMEZONE,
    )

    result = check_exit(
        position(),
        101.0,
        "2026-08-24",
        current_datetime=next_day,
    )

    assert result["exit"] is True
    assert result["exit_reason"] == "Time exit"
