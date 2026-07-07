"""
Reporting utilities for the TSX Momentum Trading backtester.
"""


def print_performance_report(stats):
    """
    Print a formatted summary of the backtest results.
    """

    print("\n" + "=" * 50)
    print("TSX MOMENTUM BACKTEST REPORT")
    print("=" * 50)

    print(f"Total Trades     : {stats['total_trades']}")
    print(f"Win Rate         : {stats['win_rate']:.2f}%")
    print(f"Average Gain     : {stats['average_gain']:.2f}%")
    print(f"Average Loss     : {stats['average_loss']:.2f}%")
    print(f"Profit Factor    : {stats['profit_factor']:.2f}")
    print(f"Total Return     : {stats['total_return_percent']:.2f}%")

    print("=" * 50)