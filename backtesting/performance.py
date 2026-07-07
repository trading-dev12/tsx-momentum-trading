"""
Performance calculations for the TSX Momentum Backtester.
"""


def calculate_performance(trades, starting_balance=10000, risk_per_trade_percent=1):
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
            "max_drawdown": 0,
        }

    wins = [t["return_pct"] for t in trades if t["return_pct"] > 0]
    losses = [t["return_pct"] for t in trades if t["return_pct"] <= 0]

    win_rate = len(wins) / len(trades) * 100
    average_gain = sum(wins) / len(wins) if wins else 0
    average_loss = sum(losses) / len(losses) if losses else 0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    balance = starting_balance
    peak_balance = starting_balance
    max_drawdown = 0

    for trade in trades:
        trade_return = trade["return_pct"]

        position_impact = trade_return * (risk_per_trade_percent / 100)

        balance *= (1 + position_impact / 100)

        if balance > peak_balance:
            peak_balance = balance

        drawdown = ((balance - peak_balance) / peak_balance) * 100

        if drawdown < max_drawdown:
            max_drawdown = drawdown

    total_return = ((balance - starting_balance) / starting_balance) * 100

    return {
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "average_gain": round(average_gain, 2),
        "average_loss": round(average_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "starting_balance": round(starting_balance, 2),
        "ending_balance": round(balance, 2),
        "total_return": round(total_return, 2),
        "max_drawdown": round(max_drawdown, 2),
    }