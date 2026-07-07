"""
Performance calculations for the TSX Momentum Backtester.
"""

def calculate_performance(trades, starting_balance=10000):
    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "average_gain": 0,
            "average_loss": 0,
            "profit_factor": 0,
            "starting_balance": starting_balance,
            "ending_balance": starting_balance,
            "total_return": 0,
        }

    wins = [t["return_pct"] for t in trades if t["return_pct"] > 0]
    losses = [t["return_pct"] for t in trades if t["return_pct"] <= 0]

    win_rate = len(wins) / len(trades) * 100

    average_gain = sum(wins) / len(wins) if wins else 0
    average_loss = sum(losses) / len(losses) if losses else 0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else 0
    )

    balance = starting_balance

    for trade in trades:
        balance *= (1 + trade["return_pct"] / 100)

    total_return = (
        (balance - starting_balance)
        / starting_balance
        * 100
    )

    return {
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "average_gain": round(average_gain, 2),
        "average_loss": round(average_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "starting_balance": round(starting_balance, 2),
        "ending_balance": round(balance, 2),
        "total_return": round(total_return, 2),
    }