"""
Performance calculations for the TSX Momentum Backtester.
"""


def calculate_performance(trades, starting_balance=10000, risk_per_trade_percent=1):
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "average_gain": 0,
            "average_loss": 0,
            "profit_factor": 0,
            "expectancy": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "starting_balance": starting_balance,
            "ending_balance": starting_balance,
            "total_return": 0,
            "max_drawdown": 0,
            "best_stock": "N/A",
            "worst_stock": "N/A",
            "exit_reasons": {},
        }

    returns = [t["return_pct"] for t in trades]

    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    total_trades = len(trades)
    winning_trades = len(wins)
    losing_trades = len(losses)

    win_rate = winning_trades / total_trades * 100
    loss_rate = losing_trades / total_trades * 100

    average_gain = sum(wins) / winning_trades if winning_trades else 0
    average_loss = sum(losses) / losing_trades if losing_trades else 0

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    expectancy = (win_rate / 100 * average_gain) + (loss_rate / 100 * average_loss)

    best_trade = max(returns)
    worst_trade = min(returns)

    balance = starting_balance
    peak_balance = starting_balance
    max_drawdown = 0

    stock_returns = {}
    exit_reasons = {}

    for trade in trades:
        symbol = trade.get("symbol", "UNKNOWN")
        trade_return = trade["return_pct"]
        exit_reason = trade.get("exit_reason", "Unknown")

        stock_returns[symbol] = stock_returns.get(symbol, 0) + trade_return
        exit_reasons[exit_reason] = exit_reasons.get(exit_reason, 0) + 1

        position_impact = trade_return * (risk_per_trade_percent / 100)
        balance *= (1 + position_impact / 100)

        if balance > peak_balance:
            peak_balance = balance

        drawdown = ((balance - peak_balance) / peak_balance) * 100

        if drawdown < max_drawdown:
            max_drawdown = drawdown

    total_return = ((balance - starting_balance) / starting_balance) * 100

    best_stock = max(stock_returns, key=stock_returns.get)
    worst_stock = min(stock_returns, key=stock_returns.get)

    return {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 2),
        "average_gain": round(average_gain, 2),
        "average_loss": round(average_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "starting_balance": round(starting_balance, 2),
        "ending_balance": round(balance, 2),
        "total_return": round(total_return, 2),
        "max_drawdown": round(max_drawdown, 2),
        "best_stock": best_stock,
        "worst_stock": worst_stock,
        "exit_reasons": exit_reasons,
    }