"""
Trade simulator for the TSX Momentum Trading backtester.
"""


def simulate_trade(rows, entry_index, hold_days=3):
    """
    Simulate a basic trade.

    Entry:
        Buy at the close of the signal day.

    Exit:
        Sell after hold_days, or the final available day.
    """

    entry_row = rows[entry_index]
    exit_index = min(entry_index + hold_days, len(rows) - 1)
    exit_row = rows[exit_index]

    entry_price = entry_row["close"]
    exit_price = exit_row["close"]

    profit_loss = exit_price - entry_price
    profit_loss_percent = (profit_loss / entry_price) * 100 if entry_price > 0 else 0

    return {
        "entry_date": entry_row["date"],
        "exit_date": exit_row["date"],
        "entry_price": entry_price,
        "exit_price": exit_price,
        "profit_loss": profit_loss,
        "profit_loss_percent": profit_loss_percent,
        "hold_days": exit_index - entry_index,
    }