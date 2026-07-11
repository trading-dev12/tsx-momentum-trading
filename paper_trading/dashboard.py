"""
Paper Trading Dashboard

Builds portfolio status, open-position details, recent trades,
and performance analytics for live paper-trading validation.
"""


def calculate_closed_trade_metrics(
    closed_trades,
    starting_cash,
):
    """
    Calculate reusable performance statistics from closed trades.
    """

    total_trades = len(closed_trades)

    winning_trades = [
        trade
        for trade in closed_trades
        if float(trade.get("profit_loss", 0)) > 0
    ]

    losing_trades = [
        trade
        for trade in closed_trades
        if float(trade.get("profit_loss", 0)) < 0
    ]

    breakeven_trades = [
        trade
        for trade in closed_trades
        if float(trade.get("profit_loss", 0)) == 0
    ]

    total_profit_loss = sum(
        float(trade.get("profit_loss", 0))
        for trade in closed_trades
    )

    total_winning_profit = sum(
        float(trade.get("profit_loss", 0))
        for trade in winning_trades
    )

    total_losing_profit = abs(
        sum(
            float(trade.get("profit_loss", 0))
            for trade in losing_trades
        )
    )

    win_rate = (
        (len(winning_trades) / total_trades) * 100
        if total_trades > 0
        else 0.0
    )

    average_winner = (
        total_winning_profit / len(winning_trades)
        if winning_trades
        else 0.0
    )

    average_loser = (
        -total_losing_profit / len(losing_trades)
        if losing_trades
        else 0.0
    )

    expectancy_percent = (
        sum(
            float(
                trade.get(
                    "profit_loss_percent",
                    0,
                )
            )
            for trade in closed_trades
        )
        / total_trades
        if total_trades > 0
        else 0.0
    )

    if total_losing_profit > 0:
        profit_factor = (
            total_winning_profit
            / total_losing_profit
        )
    elif total_winning_profit > 0:
        profit_factor = None
    else:
        profit_factor = 0.0

    best_trade = (
        max(
            closed_trades,
            key=lambda trade: float(
                trade.get(
                    "profit_loss_percent",
                    0,
                )
            ),
        )
        if closed_trades
        else None
    )

    worst_trade = (
        min(
            closed_trades,
            key=lambda trade: float(
                trade.get(
                    "profit_loss_percent",
                    0,
                )
            ),
        )
        if closed_trades
        else None
    )

    equity = float(starting_cash)
    equity_peak = equity
    maximum_drawdown = 0.0

    for trade in closed_trades:
        equity += float(
            trade.get(
                "profit_loss",
                0,
            )
        )

        equity_peak = max(
            equity_peak,
            equity,
        )

        drawdown_percent = (
            ((equity - equity_peak) / equity_peak) * 100
            if equity_peak > 0
            else 0.0
        )

        maximum_drawdown = min(
            maximum_drawdown,
            drawdown_percent,
        )

    total_closed_return = (
        (total_profit_loss / starting_cash) * 100
        if starting_cash > 0
        else 0.0
    )

    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "breakeven_trades": len(breakeven_trades),
        "win_rate": win_rate,
        "total_profit_loss": total_profit_loss,
        "total_closed_return": total_closed_return,
        "average_winner": average_winner,
        "average_loser": average_loser,
        "profit_factor": profit_factor,
        "expectancy_percent": expectancy_percent,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "maximum_drawdown": maximum_drawdown,
    }


def build_paper_dashboard_text(
    engine,
    current_prices=None,
):
    if current_prices is None:
        current_prices = {}

    summary = engine.portfolio.summary(
        current_prices
    )

    open_positions = (
        engine.portfolio.open_positions
    )

    closed_trades = (
        engine.portfolio.closed_trades
    )

    metrics = calculate_closed_trade_metrics(
        closed_trades=closed_trades,
        starting_cash=summary["starting_cash"],
    )

    divider = "-" * 44
    header_divider = "=" * 44
    lines = []

    total_open_profit_loss = 0.0

    for position in open_positions:
        symbol = position["symbol"]
        entry_price = float(
            position["entry_price"]
        )
        shares = int(
            position["shares"]
        )

        current_price = float(
            current_prices.get(
                symbol,
                entry_price,
            )
        )

        total_open_profit_loss += (
            current_price - entry_price
        ) * shares

    profit_factor = metrics["profit_factor"]

    if profit_factor is None:
        profit_factor_text = "N/A"
    else:
        profit_factor_text = (
            f"{profit_factor:.2f}"
        )

    lines.append(header_divider)
    lines.append("TSX MOMENTUM PRO")
    lines.append("PAPER TRADING ANALYTICS")
    lines.append(header_divider)

    lines.append("")
    lines.append("PORTFOLIO")
    lines.append(divider)
    lines.append(
        f"Starting Cash     "
        f"${summary['starting_cash']:>12,.2f}"
    )
    lines.append(
        f"Available Cash    "
        f"${summary['cash']:>12,.2f}"
    )
    lines.append(
        f"Portfolio Value   "
        f"${summary['portfolio_value']:>12,.2f}"
    )
    lines.append(
        f"Total Return       "
        f"{summary['total_return']:>11.2f}%"
    )

    lines.append("")
    lines.append("POSITION STATUS")
    lines.append(divider)
    lines.append(
        f"Open Positions    "
        f"{summary['open_positions']:>13}"
    )
    lines.append(
        f"Closed Trades     "
        f"{summary['closed_trades']:>13}"
    )
    lines.append(
        f"Open P/L          "
        f"${total_open_profit_loss:>12,.2f}"
    )
    lines.append(
        f"Realized P/L      "
        f"${metrics['total_profit_loss']:>12,.2f}"
    )

    lines.append("")
    lines.append("PERFORMANCE")
    lines.append(divider)

    if metrics["total_trades"] > 0:
        lines.append(
            f"Total Trades      "
            f"{metrics['total_trades']:>13}"
        )
        lines.append(
            f"Winning Trades    "
            f"{metrics['winning_trades']:>13}"
        )
        lines.append(
            f"Losing Trades     "
            f"{metrics['losing_trades']:>13}"
        )
        lines.append(
            f"Breakeven Trades  "
            f"{metrics['breakeven_trades']:>13}"
        )
        lines.append(
            f"Win Rate           "
            f"{metrics['win_rate']:>11.2f}%"
        )
        lines.append(
            f"Profit Factor      "
            f"{profit_factor_text:>12}"
        )
        lines.append(
            f"Expectancy         "
            f"{metrics['expectancy_percent']:>11.2f}%"
        )
        lines.append(
            f"Average Winner    "
            f"${metrics['average_winner']:>12,.2f}"
        )
        lines.append(
            f"Average Loser     "
            f"${metrics['average_loser']:>12,.2f}"
        )
        lines.append(
            f"Closed Return      "
            f"{metrics['total_closed_return']:>11.2f}%"
        )
        lines.append(
            f"Max Drawdown       "
            f"{metrics['maximum_drawdown']:>11.2f}%"
        )

        best_trade = metrics["best_trade"]
        worst_trade = metrics["worst_trade"]

        lines.append(
            f"Best Trade        "
            f"{best_trade['symbol']:>8} "
            f"{float(best_trade['profit_loss_percent']):>7.2f}%"
        )
        lines.append(
            f"Worst Trade       "
            f"{worst_trade['symbol']:>8} "
            f"{float(worst_trade['profit_loss_percent']):>7.2f}%"
        )
    else:
        lines.append(
            "No completed trades available."
        )

    lines.append("")
    lines.append("OPEN POSITIONS")
    lines.append(divider)

    if not open_positions:
        lines.append("No open positions.")
    else:
        for position in open_positions:
            symbol = position["symbol"]
            entry_price = float(
                position["entry_price"]
            )
            shares = int(
                position["shares"]
            )
            stop_price = float(
                position["stop_price"]
            )
            target_price = float(
                position["target_price"]
            )

            current_price = float(
                current_prices.get(
                    symbol,
                    entry_price,
                )
            )

            profit_loss = (
                current_price - entry_price
            ) * shares

            profit_loss_percent = (
                (
                    current_price
                    - entry_price
                )
                / entry_price
            ) * 100

            lines.append(
                f"{symbol} | {shares} shares"
            )
            lines.append(
                f"Entry ${entry_price:.2f} | "
                f"Current ${current_price:.2f}"
            )
            lines.append(
                f"Stop ${stop_price:.2f} | "
                f"Target ${target_price:.2f}"
            )
            lines.append(
                f"Open P/L "
                f"${profit_loss:+,.2f} "
                f"({profit_loss_percent:+.2f}%)"
            )
            lines.append("")

    lines.append("RECENT CLOSED TRADES")
    lines.append(divider)

    if not closed_trades:
        lines.append(
            "No closed trades yet."
        )
    else:
        for trade in reversed(
            closed_trades[-5:]
        ):
            lines.append(
                f"{trade['symbol']} | "
                f"{float(trade['profit_loss_percent']):+.2f}% | "
                f"${float(trade['profit_loss']):+,.2f}"
            )
            lines.append(
                f"Entry "
                f"${float(trade['entry_price']):.2f} | "
                f"Exit "
                f"${float(trade['exit_price']):.2f}"
            )
            lines.append(
                f"Reason: "
                f"{trade['exit_reason']}"
            )
            lines.append("")

    lines.append(header_divider)
    lines.append(
        "PAPER TRADING STATUS: VALIDATION ACTIVE"
    )
    lines.append(header_divider)

    return "\n".join(lines)


def display_paper_dashboard(
    engine,
    current_prices=None,
):
    print(
        build_paper_dashboard_text(
            engine,
            current_prices,
        )
    )