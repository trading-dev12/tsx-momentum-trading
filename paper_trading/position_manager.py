"""
Paper Trading Position Manager

Monitors open paper trades and closes them when stop,
target, or max holding period rules are triggered.
"""


def check_exit(position, current_price, current_date):
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

    return {
        "exit": False,
        "exit_price": None,
        "exit_date": None,
        "exit_reason": None,
    }


def monitor_positions(portfolio, current_prices, current_date):
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