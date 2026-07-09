"""
Performance calculations for backtesting results.
"""


def calculate_performance(trades, starting_balance=10000):
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
            "best_stock": None,
            "worst_stock": None,
            "exit_reasons": {},
        }

    returns = [trade.get("return_pct", trade.get("profit_loss_percent", 0)) for trade in trades]

    winning_returns = [r for r in returns if r > 0]
    losing_returns = [r for r in returns if r <= 0]

    total_trades = len(trades)
    winning_trades = len(winning_returns)
    losing_trades = len(losing_returns)

    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

    average_gain = (
        sum(winning_returns) / len(winning_returns)
        if winning_returns
        else 0
    )

    average_loss = (
        sum(losing_returns) / len(losing_returns)
        if losing_returns
        else 0
    )

    total_wins = sum(winning_returns)
    total_losses = abs(sum(losing_returns))

    profit_factor = (
        total_wins / total_losses
        if total_losses > 0
        else 999
    )

    expectancy = sum(returns) / len(returns) if returns else 0

    best_trade = max(returns) if returns else 0
    worst_trade = min(returns) if returns else 0

    balance = starting_balance
    peak_balance = starting_balance
    max_drawdown = 0

    for trade_return in returns:
        balance = balance + (starting_balance * 0.01 * trade_return)
        peak_balance = max(peak_balance, balance)

        drawdown = ((balance - peak_balance) / peak_balance) * 100

        if drawdown < max_drawdown:
            max_drawdown = drawdown

    symbol_returns = {}

    for trade in trades:
        symbol = trade.get("symbol", "UNKNOWN")
        trade_return = trade.get("return_pct", trade.get("profit_loss_percent", 0))

        if symbol not in symbol_returns:
            symbol_returns[symbol] = []

        symbol_returns[symbol].append(trade_return)

    avg_symbol_returns = {
        symbol: sum(values) / len(values)
        for symbol, values in symbol_returns.items()
        if values
    }

    best_stock = (
        max(avg_symbol_returns, key=avg_symbol_returns.get)
        if avg_symbol_returns
        else None
    )

    worst_stock = (
        min(avg_symbol_returns, key=avg_symbol_returns.get)
        if avg_symbol_returns
        else None
    )

    exit_reasons = {}

    for trade in trades:
        reason = trade.get("exit_reason", "UNKNOWN")

        if reason not in exit_reasons:
            exit_reasons[reason] = 0

        exit_reasons[reason] += 1

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
        "starting_balance": starting_balance,
        "ending_balance": round(balance, 2),
        "total_return": round(((balance - starting_balance) / starting_balance) * 100, 2),
        "max_drawdown": round(max_drawdown, 2),
        "best_stock": best_stock,
        "worst_stock": worst_stock,
        "exit_reasons": exit_reasons,
    }