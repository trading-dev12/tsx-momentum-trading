"""
Paper Trading Position Manager

Monitors open paper trades and closes them when stop,
target, or maximum holding-period rules are triggered.
"""

from datetime import datetime, timedelta


def count_trading_days(entry_date, current_date):
    """
    Count weekdays after the entry date up to the current date.

    This currently excludes Saturdays and Sundays.
    TSX market holidays will be added separately.
    """

    entry = datetime.strptime(entry_date, "%Y-%m-%d").date()
    current = datetime.strptime(current_date, "%Y-%m-%d").date()

    if current <= entry:
        return 0

    trading_days = 0
    day = entry

    while day < current:
        day += timedelta(days=1)

        if day.weekday() < 5:
            trading_days += 1

    return trading_days


def check_exit(position, current_price, current_date):
    """
    Check whether an open position should be closed.

    Exit priority matches the historical simulator:

    1. Stop loss
    2. Profit target
    3. Maximum holding period
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

    entry_date = position.get("entry_date")
    max_hold_days = position.get("max_hold_days", 10)

    if entry_date:
        trading_days_held = count_trading_days(
            entry_date,
            current_date,
        )

        if trading_days_held >= max_hold_days:
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


def monitor_positions(portfolio, current_prices, current_date):
    """
    Check every open paper position and close positions
    whose exit rules have been triggered.
    """

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
        )

        if exit_signal["exit"]:
            result = portfolio.close_position(
                symbol=symbol,
                exit_price=exit_signal["exit_price"],
                exit_date=exit_signal["exit_date"],
                exit_reason=exit_signal["exit_reason"],
            )

            if result["success"]:
                closed_trades.append(result["trade"])

    return closed_trades