"""
Strategy Comparison Engine

Runs multiple strategy configurations across the entire
research universe and compares their performance.
"""

from research.universe_backtester import run_research_universe_backtest
from backtesting.performance import calculate_performance


def compare_strategies():

    strategies = [
        {
            "name": "Baseline",
            "tmqs": 80,
            "rvol": 1.5,
            "breakout_only": True,
        },
        {
            "name": "High Quality",
            "tmqs": 90,
            "rvol": 2.0,
            "breakout_only": True,
        },
        {
            "name": "Aggressive",
            "tmqs": 70,
            "rvol": 1.2,
            "breakout_only": True,
        },
        {
            "name": "Loose",
            "tmqs": 65,
            "rvol": 1.0,
            "breakout_only": False,
        },
    ]

    print("=" * 70)
    print("TSX MOMENTUM STRATEGY COMPARISON")
    print("=" * 70)

    for strategy in strategies:

        print("\n")
        print("=" * 70)
        print(strategy["name"])
        print("=" * 70)

        trades = run_research_universe_backtest(
            min_tmqs=strategy["tmqs"],
            min_rvol=strategy["rvol"],
            breakout_only=strategy["breakout_only"],
            return_summary=True,
        )

        trades, performance = trades

        print()
        print(f"Trades: {performance['total_trades']}")
        print(f"Win Rate: {performance['win_rate']:.2f}%")
        print(f"Profit Factor: {performance['profit_factor']:.2f}")
        print(f"Expectancy: {performance['expectancy']:.2f}%")
        print(f"Return: {performance['total_return']:.2f}%")
        print(f"Drawdown: {performance['max_drawdown']:.2f}%")