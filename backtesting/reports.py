"""
Reporting utilities for the TSX Momentum Backtester.
"""

import csv


def print_performance_report(stats):
    print("\n" + "=" * 55)
    print("TSX MOMENTUM PRO BACKTEST REPORT")
    print("=" * 55)

    print(f"Starting Balance : ${stats['starting_balance']:,.2f}")
    print(f"Ending Balance   : ${stats['ending_balance']:,.2f}")
    print(f"Total Return     : {stats['total_return']:.2f}%")
    print(f"Max Drawdown     : {stats['max_drawdown']:.2f}%")
    print(f"Best Stock       : {stats['best_stock']}")
    print(f"Worst Stock      : {stats['worst_stock']}")
    print("-" * 55)

    print(f"Total Trades     : {stats['total_trades']}")
    print(f"Win Rate         : {stats['win_rate']:.2f}%")
    print(f"Average Gain     : {stats['average_gain']:.2f}%")
    print(f"Average Loss     : {stats['average_loss']:.2f}%")
    print(f"Profit Factor    : {stats['profit_factor']:.2f}")

    print("=" * 55)


def save_trade_log(trades, filename="backtesting/trade_log.csv"):
    if not trades:
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Symbol", "Return %", "Reason"])

        for trade in trades:
            writer.writerow([
                trade.get("symbol", ""),
                round(trade.get("return_pct", 0), 2),
                trade.get("reason", "")
            ])

    print(f"\nTrade log saved to {filename}")