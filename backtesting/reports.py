"""
Reporting utilities for the TSX Momentum Backtester.
"""

def print_performance_report(stats):
    print("\n" + "=" * 55)
    print("TSX MOMENTUM PRO BACKTEST REPORT")
    print("=" * 55)

    print(f"Starting Balance : ${stats['starting_balance']:,.2f}")
    print(f"Ending Balance   : ${stats['ending_balance']:,.2f}")
    print(f"Total Return     : {stats['total_return']:.2f}%")
    print(f"Max Drawdown     : {stats['max_drawdown']:.2f}%")
    print("-" * 55)

    print(f"Total Trades     : {stats['total_trades']}")
    print(f"Win Rate         : {stats['win_rate']:.2f}%")
    print(f"Average Gain     : {stats['average_gain']:.2f}%")
    print(f"Average Loss     : {stats['average_loss']:.2f}%")
    print(f"Profit Factor    : {stats['profit_factor']:.2f}")

    print("=" * 55)