"""
Trade simulator for the TSX Momentum Trading backtester.
"""


def calculate_atr(rows, current_index, period=14):
    """
    Calculate Average True Range using the previous candles.
    """

    if current_index < period:
        return None

    true_ranges = []

    for index in range(current_index - period + 1, current_index + 1):
        current = rows[index]
        previous = rows[index - 1]

        high_low = current["high"] - current["low"]
        high_close = abs(current["high"] - previous["close"])
        low_close = abs(current["low"] - previous["close"])

        true_range = max(high_low, high_close, low_close)
        true_ranges.append(true_range)

    return sum(true_ranges) / len(true_ranges)


def simulate_trade(rows, entry_index, atr_multiplier=1.5, reward_multiplier=2.0, max_hold_days=5):
    """
    Simulate a trade using ATR-based stop-loss and profit target.

    Entry:
        Buy at the close of the signal day.

    Stop:
        Entry price minus ATR x atr_multiplier.

    Target:
        Entry price plus risk x reward_multiplier.

    Exit:
        Stop hit, target hit, or max hold days.
    """

    entry_row = rows[entry_index]
    entry_price = entry_row["close"]

    atr = calculate_atr(rows, entry_index)

    if atr is None:
        return None

    stop_price = entry_price - (atr * atr_multiplier)
    risk_per_share = entry_price - stop_price
    target_price = entry_price + (risk_per_share * reward_multiplier)

    final_index = min(entry_index + max_hold_days, len(rows) - 1)

    exit_price = rows[final_index]["close"]
    exit_date = rows[final_index]["date"]
    exit_reason = "Time exit"

    for index in range(entry_index + 1, final_index + 1):
        row = rows[index]

        if row["low"] <= stop_price:
            exit_price = stop_price
            exit_date = row["date"]
            exit_reason = "Stop hit"
            break

        if row["high"] >= target_price:
            exit_price = target_price
            exit_date = row["date"]
            exit_reason = "Target hit"
            break

    profit_loss = exit_price - entry_price
    profit_loss_percent = (profit_loss / entry_price) * 100 if entry_price > 0 else 0

    return {
        "entry_date": entry_row["date"],
        "exit_date": exit_date,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "atr": atr,
        "profit_loss": profit_loss,
        "profit_loss_percent": profit_loss_percent,
        "hold_days": final_index - entry_index,
        "exit_reason": exit_reason,
    }