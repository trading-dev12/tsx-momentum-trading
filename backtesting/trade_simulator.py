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
    """
    Simulate a trade without same-bar look-ahead bias.

    The setup is identified using the completed candle at entry_index.
    The trade is entered at the next trading day's opening price.
    ATR is calculated using information available through the signal day.
    """

    signal_index = entry_index
    actual_entry_index = signal_index + 1

    # A next-day entry is impossible if the signal occurs
    # on the final historical row.
    if actual_entry_index >= len(rows):
        return None

    signal_row = rows[signal_index]
    entry_row = rows[actual_entry_index]
    
    
    raw_entry_price = entry_row["open"]
    entry_price = raw_entry_price * (1 + slippage_percent)

    # ATR must only use information available on or before
    # the completed signal day.
    atr = calculate_atr(rows, signal_index)

    if atr is None:
        return None

    stop_price = entry_price - (atr * atr_multiplier)
    risk_per_share = entry_price - stop_price
    target_price = entry_price + (
        risk_per_share * reward_multiplier
    )

    # The entry session counts as holding day 1.
    final_index = min(
        actual_entry_index + max_hold_days - 1,
        len(rows) - 1,
    )

    exit_price = rows[final_index]["close"]
    exit_date = rows[final_index]["date"]
    exit_reason = "Time exit"
    actual_exit_index = final_index

    # Because entry occurs at the next day's open, the stop
    # or target can be reached during that same trading session.
    for index in range(actual_entry_index, final_index + 1):
        row = rows[index]

        # Stop is checked first as the conservative assumption
        # if both stop and target fall inside one daily candle.
        if row["low"] <= stop_price:
            exit_price = stop_price
            exit_date = row["date"]
            exit_reason = "Stop hit"
            actual_exit_index = index
            break

        if row["high"] >= target_price:
            exit_price = target_price
            exit_date = row["date"]
            exit_reason = "Target hit"
            actual_exit_index = index
            break

    exit_price = exit_price * (1 - slippage_percent)

    profit_loss = exit_price - entry_price

    if entry_price > 0:
        profit_loss_percent = (
            profit_loss / entry_price
        ) * 100
    else:
        profit_loss_percent = 0

    return {
        "signal_date": signal_row["date"],
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
        "hold_days": actual_exit_index - actual_entry_index + 1,
        "exit_reason": exit_reason,
    }