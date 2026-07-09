"""
Trade simulator for historical backtesting.
"""


def calculate_atr(rows, index, period=14):
    if index < period:
        return None

    true_ranges = []

    for i in range(index - period + 1, index + 1):
        high = rows[i]["high"]
        low = rows[i]["low"]
        previous_close = rows[i - 1]["close"]

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close),
        )

        true_ranges.append(true_range)

    return sum(true_ranges) / len(true_ranges)


def simulate_trade(
    rows,
    entry_index,
    atr_multiplier=2.0,
    reward_multiplier=2.5,
    max_hold_days=10,
    slippage_percent=0.0,
):
    entry_row = rows[entry_index]

    raw_entry_price = entry_row["close"]
    entry_price = raw_entry_price * (1 + slippage_percent)

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

    exit_price = exit_price * (1 - slippage_percent)

    profit_loss = exit_price - entry_price

    if entry_price > 0:
        profit_loss_percent = (profit_loss / entry_price) * 100
    else:
        profit_loss_percent = 0

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
        "return_pct": profit_loss_percent,
        "hold_days": final_index - entry_index,
        "exit_reason": exit_reason,
    }