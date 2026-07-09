"""
Paper Trading Dashboard

Builds and displays portfolio status, open positions,
closed trades, and current paper trading summary.
"""


def build_paper_dashboard_text(engine, current_prices=None):
    if current_prices is None:
        current_prices = {}

    summary = engine.portfolio.summary(current_prices)

    lines = []

    lines.append("=" * 70)
    lines.append("TSX MOMENTUM PRO - PAPER TRADING DASHBOARD")
    lines.append("=" * 70)

    lines.append("")
    lines.append("PORTFOLIO SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Starting Cash:   ${summary['starting_cash']:,.2f}")
    lines.append(f"Cash:            ${summary['cash']:,.2f}")
    lines.append(f"Portfolio Value: ${summary['portfolio_value']:,.2f}")
    lines.append(f"Total Return:    {summary['total_return']:.2f}%")
    lines.append(f"Open Positions:  {summary['open_positions']}")
    lines.append(f"Closed Trades:   {summary['closed_trades']}")

    lines.append("")
    lines.append("OPEN POSITIONS")
    lines.append("-" * 70)

    if not engine.portfolio.open_positions:
        lines.append("No open positions.")
    else:
        for position in engine.portfolio.open_positions:
            symbol = position["symbol"]
            entry_price = position["entry_price"]
            shares = position["shares"]
            stop_price = position["stop_price"]
            target_price = position["target_price"]
            current_price = current_prices.get(symbol, entry_price)

            profit_loss = (current_price - entry_price) * shares
            profit_loss_percent = ((current_price - entry_price) / entry_price) * 100

            lines.append(f"{symbol}")
            lines.append(f"  Shares:        {shares}")
            lines.append(f"  Entry Price:   ${entry_price:.2f}")
            lines.append(f"  Current Price: ${current_price:.2f}")
            lines.append(f"  Stop Price:    ${stop_price:.2f}")
            lines.append(f"  Target Price:  ${target_price:.2f}")
            lines.append(
                f"  Open P/L:      ${profit_loss:.2f} "
                f"({profit_loss_percent:.2f}%)"
            )
            lines.append("")

    lines.append("")
    lines.append("CLOSED TRADES")
    lines.append("-" * 70)

    if not engine.portfolio.closed_trades:
        lines.append("No closed trades yet.")
    else:
        for trade in engine.portfolio.closed_trades[-5:]:
            lines.append(
                f"{trade['symbol']} | "
                f"Entry: ${trade['entry_price']:.2f} | "
                f"Exit: ${trade['exit_price']:.2f} | "
                f"P/L: ${trade['profit_loss']:.2f} "
                f"({trade['profit_loss_percent']:.2f}%) | "
                f"{trade['exit_reason']}"
            )

    lines.append("=" * 70)

    return "\n".join(lines)


def display_paper_dashboard(engine, current_prices=None):
    print(build_paper_dashboard_text(engine, current_prices))