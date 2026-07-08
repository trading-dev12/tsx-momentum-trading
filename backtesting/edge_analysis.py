"""
TMQS Edge Analysis Tool.

Analyzes how TMQS thresholds affect trade quality.
"""

from collections import Counter

from backtesting.backtester import run_watchlist_backtest


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def calculate_trade_details(trades):
    if not trades:
        return {
            "average_tmqs": 0,
            "average_rvol": 0,
            "median_rvol": 0,
            "min_rvol": 0,
            "max_rvol": 0,
            "breakout_counts": Counter(),
        }

    tmqs_values = [trade.get("tmqs", 0) for trade in trades]
    rvol_values = sorted(trade.get("rvol", 0) for trade in trades)
    breakout_counts = Counter(trade.get("breakout", "UNKNOWN") for trade in trades)

    middle_index = len(rvol_values) // 2

    return {
        "average_tmqs": sum(tmqs_values) / len(tmqs_values),
        "average_rvol": sum(rvol_values) / len(rvol_values),
        "median_rvol": rvol_values[middle_index],
        "min_rvol": min(rvol_values),
        "max_rvol": max(rvol_values),
        "breakout_counts": breakout_counts,
    }


def main():
    print_section("TSX MOMENTUM PRO - TMQS EDGE ANALYSIS")

    tmqs_levels = [80, 85, 90, 95]

    atr_multiplier = 2.0
    reward_multiplier = 2.5
    max_hold_days = 10

    print("Using baseline trade management:")
    print(f"ATR Multiplier    : {atr_multiplier}")
    print(f"Reward Multiplier : {reward_multiplier}")
    print(f"Max Hold Days     : {max_hold_days}")

    results = []

    for tmqs in tmqs_levels:
        trades, stats = run_watchlist_backtest(
            min_tmqs=tmqs,
            min_rvol=1.0,
            breakout_only=True,
            atr_multiplier=atr_multiplier,
            reward_multiplier=reward_multiplier,
            max_hold_days=max_hold_days,
            show_report=False,
            save_log=False,
            verbose=False,
        )

        details = calculate_trade_details(trades)

        results.append(
            {
                "tmqs": tmqs,
                "trades": stats["total_trades"],
                "return": stats["total_return"],
                "win_rate": stats["win_rate"],
                "profit_factor": stats["profit_factor"],
                "expectancy": stats["expectancy"],
                "max_drawdown": stats["max_drawdown"],
                "average_tmqs": details["average_tmqs"],
                "average_rvol": details["average_rvol"],
                "median_rvol": details["median_rvol"],
                "min_rvol": details["min_rvol"],
                "max_rvol": details["max_rvol"],
                "breakout_counts": details["breakout_counts"],
            }
        )

    print_section("TMQS THRESHOLD COMPARISON")

    for row in results:
        print(f"\nTMQS >= {row['tmqs']}")
        print("-" * 70)
        print(f"Trades          : {row['trades']}")
        print(f"Return          : {row['return']:.2f}%")
        print(f"Win Rate        : {row['win_rate']:.2f}%")
        print(f"Profit Factor   : {row['profit_factor']:.2f}")
        print(f"Expectancy      : {row['expectancy']:.2f}%")
        print(f"Max Drawdown    : {row['max_drawdown']:.2f}%")
        print(f"Average TMQS    : {row['average_tmqs']:.2f}")
        print(f"Average RVOL    : {row['average_rvol']:.2f}")
        print(f"Median RVOL     : {row['median_rvol']:.2f}")
        print(f"RVOL Range      : {row['min_rvol']:.2f} - {row['max_rvol']:.2f}")

        print("\nBreakout Types:")
        for breakout, count in row["breakout_counts"].items():
            print(f"  {breakout:<18}: {count}")

    print_section("EDGE ANALYSIS SUMMARY")

    print("Higher TMQS thresholds should ideally show:")
    print("- Fewer trades")
    print("- Higher average TMQS")
    print("- Stronger average RVOL")
    print("- Higher Profit Factor")
    print("- Higher Expectancy")
    print("- Lower or controlled drawdown")


if __name__ == "__main__":
    main()