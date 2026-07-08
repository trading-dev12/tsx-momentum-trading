"""
Reporting utilities for the TSX Momentum Backtester.
"""

import csv


def print_performance_report(stats):
    print("\n" + "=" * 60)
    print("TSX MOMENTUM PRO BACKTEST REPORT")
    print("=" * 60)

    print(f"Starting Balance : ${stats['starting_balance']:,.2f}")
    print(f"Ending Balance   : ${stats['ending_balance']:,.2f}")
    print(f"Total Return     : {stats['total_return']:.2f}%")
    print(f"Max Drawdown     : {stats['max_drawdown']:.2f}%")
    print("-" * 60)

    print(f"Total Trades     : {stats['total_trades']}")
    print(f"Winning Trades   : {stats['winning_trades']}")
    print(f"Losing Trades    : {stats['losing_trades']}")
    print(f"Win Rate         : {stats['win_rate']:.2f}%")
    print(f"Average Gain     : {stats['average_gain']:.2f}%")
    print(f"Average Loss     : {stats['average_loss']:.2f}%")
    print(f"Profit Factor    : {stats['profit_factor']:.2f}")
    print(f"Expectancy       : {stats['expectancy']:.2f}%")
    print(f"Best Trade       : {stats['best_trade']:.2f}%")
    print(f"Worst Trade      : {stats['worst_trade']:.2f}%")
    print("-" * 60)

    print(f"Best Stock       : {stats['best_stock']}")
    print(f"Worst Stock      : {stats['worst_stock']}")

    print("=" * 60)


def save_trade_log(trades, filename="backtesting/trade_log.csv"):
    if not trades:
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow([
            "Symbol",
            "Entry Date",
            "Exit Date",
            "Entry Price",
            "Exit Price",
            "Stop Price",
            "Target Price",
            "ATR",
            "Hold Days",
            "Return %",
            "Profit/Loss",
            "Exit Reason",
            "Setup Reason",
        ])

        for trade in trades:
            writer.writerow([
                trade.get("symbol", ""),
                trade.get("entry_date", ""),
                trade.get("exit_date", ""),
                round(trade.get("entry_price", 0), 2),
                round(trade.get("exit_price", 0), 2),
                round(trade.get("stop_price", 0), 2),
                round(trade.get("target_price", 0), 2),
                round(trade.get("atr", 0), 2),
                trade.get("hold_days", ""),
                round(trade.get("return_pct", 0), 2),
                round(trade.get("profit_loss", 0), 2),
                trade.get("exit_reason", ""),
                trade.get("reason", ""),
            ])

    print(f"\nTrade log saved to {filename}")