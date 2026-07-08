"""
Parameter optimizer for the TSX Momentum Trading system.

Optimizer v2 tests:
- TMQS
- RVOL
- Breakout only
- ATR multiplier
- Reward multiplier
- Maximum hold days
"""

import csv

from backtesting.backtester import run_watchlist_backtest


print("=" * 70)
print("TSX MOMENTUM PRO OPTIMIZER V2")
print("=" * 70)

best_return = -999
best_profit_factor = -999
best_expectancy = -999

best_return_stats = None
best_pf_stats = None
best_expectancy_stats = None

best_return_settings = None
best_pf_settings = None
best_expectancy_settings = None

results = []

tmqs_values = [60, 65, 70, 75, 80]
rvol_values = [1.0, 1.5, 2.0]
breakout_values = [True, False]
atr_values = [1.0, 1.5, 2.0]
reward_values = [1.5, 2.0, 2.5]
hold_values = [5, 7, 10]

total_tests = (
    len(tmqs_values)
    * len(rvol_values)
    * len(breakout_values)
    * len(atr_values)
    * len(reward_values)
    * len(hold_values)
)

test_number = 0

for tmqs in tmqs_values:
    for rvol in rvol_values:
        for breakout in breakout_values:
            for atr_multiplier in atr_values:
                for reward_multiplier in reward_values:
                    for max_hold_days in hold_values:
                        test_number += 1

                        print("\n" + "-" * 70)
                        print(
                            f"Test {test_number}/{total_tests} | "
                            f"TMQS={tmqs} | "
                            f"RVOL={rvol} | "
                            f"Breakout={breakout} | "
                            f"ATR={atr_multiplier} | "
                            f"Reward={reward_multiplier} | "
                            f"Hold={max_hold_days}"
                        )

                        trades, stats = run_watchlist_backtest(
                            min_tmqs=tmqs,
                            min_rvol=rvol,
                            breakout_only=breakout,
                            atr_multiplier=atr_multiplier,
                            reward_multiplier=reward_multiplier,
                            max_hold_days=max_hold_days,
                            show_report=False,
                            save_log=False,
                            verbose=False,
                        )

                        print(
                            f"Return: {stats['total_return']:.2f}% | "
                            f"Trades: {stats['total_trades']} | "
                            f"Win Rate: {stats['win_rate']:.2f}% | "
                            f"PF: {stats['profit_factor']:.2f} | "
                            f"Expectancy: {stats['expectancy']:.2f}% | "
                            f"DD: {stats['max_drawdown']:.2f}%"
                        )

                        row = {
                            "TMQS": tmqs,
                            "RVOL": rvol,
                            "Breakout Only": breakout,
                            "ATR Multiplier": atr_multiplier,
                            "Reward Multiplier": reward_multiplier,
                            "Max Hold Days": max_hold_days,
                            "Return": stats["total_return"],
                            "Trades": stats["total_trades"],
                            "Win Rate": stats["win_rate"],
                            "Profit Factor": stats["profit_factor"],
                            "Expectancy": stats["expectancy"],
                            "Max Drawdown": stats["max_drawdown"],
                        }

                        results.append(row)

                        if stats["total_return"] > best_return:
                            best_return = stats["total_return"]
                            best_return_stats = stats
                            best_return_settings = row

                        if (
                            stats["profit_factor"] > best_profit_factor
                            and stats["total_trades"] >= 100
                        ):
                            best_profit_factor = stats["profit_factor"]
                            best_pf_stats = stats
                            best_pf_settings = row

                        if (
                            stats["expectancy"] > best_expectancy
                            and stats["total_trades"] >= 100
                        ):
                            best_expectancy = stats["expectancy"]
                            best_expectancy_stats = stats
                            best_expectancy_settings = row


def print_best_section(title, settings, stats):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    if settings is None or stats is None:
        print("No valid result found.")
        return

    print(f"TMQS              : {settings['TMQS']}")
    print(f"RVOL              : {settings['RVOL']}")
    print(f"Breakout Only     : {settings['Breakout Only']}")
    print(f"ATR Multiplier    : {settings['ATR Multiplier']}")
    print(f"Reward Multiplier : {settings['Reward Multiplier']}")
    print(f"Max Hold Days     : {settings['Max Hold Days']}")
    print("-" * 70)
    print(f"Return            : {stats['total_return']:.2f}%")
    print(f"Trades            : {stats['total_trades']}")
    print(f"Win Rate          : {stats['win_rate']:.2f}%")
    print(f"Profit Factor     : {stats['profit_factor']:.2f}")
    print(f"Expectancy        : {stats['expectancy']:.2f}%")
    print(f"Max Drawdown      : {stats['max_drawdown']:.2f}%")


print_best_section("BEST RETURN SETTINGS", best_return_settings, best_return_stats)
print_best_section("BEST PROFIT FACTOR SETTINGS", best_pf_settings, best_pf_stats)
print_best_section("BEST EXPECTANCY SETTINGS", best_expectancy_settings, best_expectancy_stats)

results = sorted(
    results,
    key=lambda x: x["Return"],
    reverse=True
)

with open("backtesting/optimizer_results.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "TMQS",
            "RVOL",
            "Breakout Only",
            "ATR Multiplier",
            "Reward Multiplier",
            "Max Hold Days",
            "Return",
            "Trades",
            "Win Rate",
            "Profit Factor",
            "Expectancy",
            "Max Drawdown",
        ],
    )

    writer.writeheader()
    writer.writerows(results)

print("\nOptimizer results saved to:")
print("backtesting/optimizer_results.csv")

print("\n")
print("=" * 90)
print("TOP 10 PARAMETER COMBINATIONS BY RETURN")
print("=" * 90)

for rank, row in enumerate(results[:10], start=1):
    print(
        f"{rank:>2}. "
        f"TMQS={row['TMQS']:>2} | "
        f"RVOL={row['RVOL']} | "
        f"Breakout={row['Breakout Only']} | "
        f"ATR={row['ATR Multiplier']} | "
        f"Reward={row['Reward Multiplier']} | "
        f"Hold={row['Max Hold Days']} | "
        f"Return={row['Return']:.2f}% | "
        f"PF={row['Profit Factor']:.2f} | "
        f"Exp={row['Expectancy']:.2f}% | "
        f"Trades={row['Trades']}"
    )