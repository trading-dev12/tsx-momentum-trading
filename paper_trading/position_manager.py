"""
Paper Trading Position Manager

Monitors open paper trades and closes them when stop,
target, or maximum holding-period rules are triggered.
"""

from datetime import datetime, timedelta
from core.market_hours import (
    TORONTO_TIMEZONE,
    get_tsx_market_close_time,
    is_tsx_trading_day,
)


def count_trading_days(entry_date, current_date):
    """
    Count weekdays from the entry date through the current date,
    including the entry date as trading day 1.

    This currently excludes Saturdays and Sundays.
    TSX market holidays will be added separately.
    """

    entry = datetime.strptime(entry_date, "%Y-%m-%d").date()
    current = datetime.strptime(current_date, "%Y-%m-%d").date()

    if current < entry:
        return 0

    trading_days = 0
    day = entry

    while day <= current:
        if is_tsx_trading_day(day):
            trading_days += 1

        day += timedelta(days=1)

    return trading_days


def check_exit(
    position,
    current_price,
    current_date,
    current_datetime=None,
):
    """
    Check whether an open position should be closed.

    Exit priority matches the historical simulator:

    1. Stop loss
    2. Profit target
    3. Maximum holding period

    The entry session counts as Day 1.

    On the exact maximum-hold day, stop and target monitoring
    remain active through the full trading session. A time exit
    becomes eligible only at the TSX close.

    Positions already beyond their maximum holding period are
    immediately eligible for a recovery time exit.
    """

    if current_price <= position["stop_price"]:
        return {
            "exit": True,
            "exit_price": position["stop_price"],
            "exit_date": current_date,
            "exit_reason": "Stop hit",
        }

    if current_price >= position["target_price"]:
        return {
            "exit": True,
            "exit_price": position["target_price"],
            "exit_date": current_date,
            "exit_reason": "Target hit",
        }

    entry_date = position.get(
        "entry_date"
    )

    max_hold_days = int(
        position.get(
            "max_hold_days",
            10,
        )
        or 10
    )

    if entry_date:
        trading_days_held = (
            count_trading_days(
                entry_date,
                current_date,
            )
        )

        time_exit_due = (
            trading_days_held
            >= max_hold_days
        )

        if (
            time_exit_due
            and trading_days_held
            == max_hold_days
            and current_datetime is not None
        ):
            if current_datetime.tzinfo is None:
                current_datetime = (
                    current_datetime.replace(
                        tzinfo=TORONTO_TIMEZONE
                    )
                )
            else:
                current_datetime = (
                    current_datetime.astimezone(
                        TORONTO_TIMEZONE
                    )
                )

            trading_date = (
                datetime.strptime(
                    current_date,
                    "%Y-%m-%d",
                ).date()
            )

            market_close_time = (
                get_tsx_market_close_time(
                    trading_date
                )
            )

            monitor_date = (
                current_datetime.date()
            )

            monitor_time = (
                current_datetime.time()
                .replace(
                    tzinfo=None
                )
            )

            if (
                monitor_date < trading_date
                or (
                    monitor_date
                    == trading_date
                    and monitor_time
                    < market_close_time
                )
            ):
                time_exit_due = False

        if time_exit_due:
            return {
                "exit": True,
                "exit_price": current_price,
                "exit_date": current_date,
                "exit_reason": "Time exit",
            }

    return {
        "exit": False,
        "exit_price": None,
        "exit_date": None,
        "exit_reason": None,
    }


def monitor_positions(
    portfolio,
    current_prices,
    current_date,
    current_datetime=None,
):
    """
    Check every open paper position and close positions
    whose exit rules have been triggered.
    """

    if current_datetime is None:
        current_datetime = datetime.now(
            TORONTO_TIMEZONE
        )

    elif current_datetime.tzinfo is None:
        current_datetime = (
            current_datetime.replace(
                tzinfo=TORONTO_TIMEZONE
            )
        )

    else:
        current_datetime = (
            current_datetime.astimezone(
                TORONTO_TIMEZONE
            )
        )

    exit_timestamp = (
        current_datetime.isoformat(
            timespec="seconds"
        )
    )

    closed_trades = []

    for position in portfolio.open_positions.copy():
        symbol = position["symbol"]

        if symbol not in current_prices:
            continue

        current_price = current_prices[symbol]

        exit_signal = check_exit(
            position,
            current_price,
            current_date,
            current_datetime=current_datetime,
        )
        print(
            f"{symbol}: exit={exit_signal['exit']} "
            f"reason={exit_signal.get('exit_reason', 'None')}"
        )

    

        if exit_signal["exit"]:
            print(
                f"Closing {symbol} at {current_price}"
            )
            result = portfolio.close_position(
                symbol=symbol,
                exit_price=exit_signal["exit_price"],
                exit_date=exit_signal["exit_date"],
                exit_reason=exit_signal["exit_reason"],
                exit_timestamp=exit_timestamp,
            )

            if result["success"]:
                closed_trades.append(result["trade"])

    return closed_trades