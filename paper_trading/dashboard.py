"""
Paper Trading Dashboard

Builds and displays portfolio status, open positions,
closed trades, and current paper trading summary.
"""


def build_paper_dashboard_text(engine, current_prices=None):
    if current_prices is None:
        current_prices = {}

    summary = engine.portfolio.summary(current_prices)
    open_positions = engine.portfolio.open_positions
    closed_trades = engine.portfolio.closed_trades

    divider = "-" * 44
    header_divider = "=" * 44
    lines = []

    # Calculate total unrealized profit/loss.
    total_open_profit_loss = 0.0

    for position in open_positions:
        symbol = position["symbol"]
        entry_price = position["entry_price"]
        shares = position["shares"]
        current_price = current_prices.get(symbol, entry_price)

        total_open_profit_loss += (
            current_price - entry_price
        ) * shares

    # Calculate closed-trade performance.
    winning_trades = [
        trade
        for trade in closed_trades
        if trade.get("profit_loss", 0) > 0
    ]

    losing_trades = [
        trade
        for trade in closed_trades
        if trade.get("profit_loss", 0) < 0
    ]

    total_closed_profit_loss = sum(
        trade.get("profit_loss", 0)
        for trade in closed_trades
    )

    if closed_trades:
        win_rate = (
            len(winning_trades) / len(closed_trades)
        ) * 100

        expectancy = sum(
            trade.get("profit_loss_percent", 0)
            for trade in closed_trades
        ) / len(closed_trades)
    else:
        win_rate = 0.0
        expectancy = 0.0

    total_winning_profit = sum(
        trade.get("profit_loss", 0)
        for trade in winning_trades
    )

    total_losing_profit = abs(
        sum(
            trade.get("profit_loss", 0)
            for trade in losing_trades
        )
    )

    if total_losing_profit > 0:
        profit_factor = (
            total_winning_profit / total_losing_profit
        )
        profit_factor_text = f"{profit_factor:.2f}"
    elif total_winning_profit > 0:
        profit_factor_text = "N/A"
    else:
        profit_factor_text = "--"

    lines.append(header_divider)
    lines.append("TSX MOMENTUM PRO")
    lines.append("TRADER CONTROL CENTER")
    lines.append(header_divider)

    lines.append("")
    lines.append("PORTFOLIO")
    lines.append(divider)
    lines.append(
        f"Starting Cash     ${summary['starting_cash']:>12,.2f}"
    )
    lines.append(
        f"Available Cash    ${summary['cash']:>12,.2f}"
    )
    lines.append(
        f"Portfolio Value   ${summary['portfolio_value']:>12,.2f}"
    )
    lines.append(
        f"Total Return       {summary['total_return']:>11.2f}%"
    )

    lines.append("")
    lines.append("POSITION STATUS")
    lines.append(divider)
    lines.append(
        f"Open Positions    {summary['open_positions']:>13}"
    )
    lines.append(
        f"Closed Trades     {summary['closed_trades']:>13}"
    )
    lines.append(
        f"Open P/L          ${total_open_profit_loss:>12,.2f}"
    )
    lines.append(
        f"Realized P/L      ${total_closed_profit_loss:>12,.2f}"
    )

    lines.append("")
    lines.append("PERFORMANCE")
    lines.append(divider)

    if closed_trades:
        lines.append(
            f"Winning Trades    {len(winning_trades):>13}"
        )
        lines.append(
            f"Losing Trades     {len(losing_trades):>13}"
        )
        lines.append(
            f"Win Rate           {win_rate:>11.2f}%"
        )
        lines.append(
            f"Profit Factor      {profit_factor_text:>12}"
        )
        lines.append(
            f"Expectancy         {expectancy:>11.2f}%"
        )
    else:
        lines.append("Win Rate                      --")
        lines.append("Profit Factor                 --")
        lines.append("Expectancy                    --")

    lines.append("")
    lines.append("OPEN POSITIONS")
    lines.append(divider)

    if not open_positions:
        lines.append("No open positions.")
    else:
        for position in open_positions:
            symbol = position["symbol"]
            entry_price = position["entry_price"]
            shares = position["shares"]
            stop_price = position["stop_price"]
            target_price = position["target_price"]
            current_price = current_prices.get(
                symbol,
                entry_price,
            )

            profit_loss = (
                current_price - entry_price
            ) * shares

            profit_loss_percent = (
                (current_price - entry_price)
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
                f"Stop  ${stop_price:.2f} | "
                f"Target  ${target_price:.2f}"
            )
            lines.append(
                f"Open P/L ${profit_loss:,.2f} "
                f"({profit_loss_percent:+.2f}%)"
            )
            lines.append("")

    lines.append("RECENT CLOSED TRADES")
    lines.append(divider)

    if not closed_trades:
        lines.append("No closed trades yet.")
    else:
        for trade in reversed(closed_trades[-5:]):
            lines.append(
                f"{trade['symbol']} | "
                f"{trade['profit_loss_percent']:+.2f}% | "
                f"${trade['profit_loss']:+,.2f}"
            )
            lines.append(
                f"Entry ${trade['entry_price']:.2f} | "
                f"Exit ${trade['exit_price']:.2f}"
            )
            lines.append(
                f"Reason: {trade['exit_reason']}"
            )
            lines.append("")

    lines.append(header_divider)
    lines.append("PAPER TRADING STATUS: READY")
    lines.append(header_divider)

    return "\n".join(lines)

def display_paper_dashboard(engine, current_prices=None):
    print(build_paper_dashboard_text(engine, current_prices))