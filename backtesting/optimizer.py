"""
Parameter optimizer for the TSX Momentum Trading system.
"""

import csv

from backtesting.backtester import run_watchlist_backtest


print("=" * 60)
print("TSX MOMENTUM PRO OPTIMIZER")
print("=" * 60)

best_return = -999
best_profit_factor = -999

best_return_stats = None
best_pf_stats = None

best_return_settings = None
best_pf_settings = None

results = []

for tmqs in range(60, 100, 5):
    for rvol in [1.0, 1.5, 2.0, 2.5]:
        for breakout in [True, False]:

            print("\n" + "-" * 60)
            print(f"Testing TMQS={tmqs} RVOL={rvol} Breakout={breakout}")

            trades, stats = run_watchlist_backtest(
                min_tmqs=tmqs,
                min_rvol=rvol,
                breakout_only=breakout,
            )

            print(
                f"Return: {stats['total_return']:.2f}% | "
                f"Trades: {stats['total_trades']} | "
                f"Win Rate: {stats['win_rate']:.2f}% | "
                f"PF: {stats['profit_factor']:.2f}"
            )

            results.append({
                "TMQS": tmqs,
                "RVOL": rvol,
                "Breakout Only": breakout,
                "Return": stats["total_return"],
                "Trades": stats["total_trades"],
                "Win Rate": stats["win_rate"],
                "Profit Factor": stats["profit_factor"],
                "Max Drawdown": stats["max_drawdown"],
            })

            if stats["total_return"] > best_return:
                best_return = stats["total_return"]
                best_return_stats = stats
                best_return_settings = (tmqs, rvol, breakout)

            if stats["profit_factor"] > best_profit_factor and stats["total_trades"] >= 100:
                best_profit_factor = stats["profit_factor"]
                best_pf_stats = stats
                best_pf_settings = (tmqs, rvol, breakout)


print("\n" + "=" * 60)
print("BEST RETURN SETTINGS")
print("=" * 60)
print(f"TMQS        : {best_return_settings[0]}")
print(f"RVOL        : {best_return_settings[1]}")
print(f"Breakout    : {best_return_settings[2]}")
print(f"Return      : {best_return_stats['total_return']:.2f}%")
print(f"Trades      : {best_return_stats['total_trades']}")
print(f"Win Rate    : {best_return_stats['win_rate']:.2f}%")
print(f"Profit Fact.: {best_return_stats['profit_factor']:.2f}")


print("\n" + "=" * 60)
print("BEST PROFIT FACTOR SETTINGS")
print("=" * 60)
print(f"TMQS        : {best_pf_settings[0]}")
print(f"RVOL        : {best_pf_settings[1]}")
print(f"Breakout    : {best_pf_settings[2]}")
print(f"Return      : {best_pf_stats['total_return']:.2f}%")
print(f"Trades      : {best_pf_stats['total_trades']}")
print(f"Win Rate    : {best_pf_stats['win_rate']:.2f}%")
print(f"Profit Fact.: {best_pf_stats['profit_factor']:.2f}")

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
            "Return",
            "Trades",
            "Win Rate",
            "Profit Factor",
            "Max Drawdown",
        ],
    )

    writer.writeheader()
    writer.writerows(results)

print("\nOptimizer results saved to:")
print("backtesting/optimizer_results.csv")
print("\n")
print("=" * 80)
print("TOP 10 PARAMETER COMBINATIONS")
print("=" * 80)

for rank, row in enumerate(results[:10], start=1):
    print(
        f"{rank:>2}. "
        f"TMQS={row['TMQS']:>2} | "
        f"RVOL={row['RVOL']} | "
        f"Breakout={row['Breakout Only']} | "
        f"Return={row['Return']:.2f}% | "
        f"PF={row['Profit Factor']:.2f} | "
        f"Trades={row['Trades']}"
    )