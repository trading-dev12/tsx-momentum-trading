"""
Symbol analysis tool for the TSX Momentum Trading system.
"""

from backtesting.backtester import run_watchlist_backtest


MIN_SAMPLE_SIZE = 5


def get_trade_return(trade):
    possible_keys = [
        "return_percent",
        "return_pct",
        "return",
        "profit_percent",
        "gain_percent",
    ]

    for key in possible_keys:
        if key in trade:
            return float(trade[key])

    return 0.0


def calculate_symbol_stats(trades):
    stats = {}

    for trade in trades:
        symbol = trade.get("symbol", "UNKNOWN")
        result = get_trade_return(trade)

        if symbol not in stats:
            stats[symbol] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "returns": [],
                "winning_returns": [],
                "losing_returns": [],
                "best": result,
                "worst": result,
            }

        stats[symbol]["trades"] += 1
        stats[symbol]["returns"].append(result)
        stats[symbol]["best"] = max(stats[symbol]["best"], result)
        stats[symbol]["worst"] = min(stats[symbol]["worst"], result)

        if result > 0:
            stats[symbol]["wins"] += 1
            stats[symbol]["winning_returns"].append(result)
        else:
            stats[symbol]["losses"] += 1
            stats[symbol]["losing_returns"].append(result)

    return stats


def rate_symbol(trades, profit_factor, expectancy):
    if trades < MIN_SAMPLE_SIZE:
        return "LOW SAMPLE"

    if profit_factor >= 2.0 and expectancy >= 3.0:
        return "STRONG"

    if profit_factor >= 1.5 and expectancy > 1.0:
        return "GOOD"

    if profit_factor >= 1.0 and expectancy > 0:
        return "WEAK EDGE"

    return "AVOID"


def build_ranked_symbols(stats):
    ranked_symbols = []

    for symbol, s in stats.items():
        trades = s["trades"]
        wins = s["wins"]

        win_rate = (wins / trades) * 100 if trades > 0 else 0
        avg_return = sum(s["returns"]) / trades if trades > 0 else 0

        total_wins = sum(s["winning_returns"])
        total_losses = abs(sum(s["losing_returns"]))

        profit_factor = total_wins / total_losses if total_losses > 0 else 999
        expectancy = avg_return

        rating = rate_symbol(trades, profit_factor, expectancy)

        ranked_symbols.append(
            {
                "symbol": symbol,
                "trades": trades,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "expectancy": expectancy,
                "avg_return": avg_return,
                "best": s["best"],
                "worst": s["worst"],
                "rating": rating,
            }
        )

    ranked_symbols.sort(
        key=lambda x: (
            x["rating"] == "STRONG",
            x["rating"] == "GOOD",
            x["rating"] == "WEAK EDGE",
            x["expectancy"],
            x["profit_factor"],
            x["win_rate"],
            x["trades"],
        ),
        reverse=True,
    )

    return ranked_symbols


def print_symbol_analysis(stats):
    ranked_symbols = build_ranked_symbols(stats)

    print("=" * 92)
    print("TSX MOMENTUM PRO - SYMBOL ANALYSIS")
    print("=" * 92)

    print(
        f"{'Symbol':<10}"
        f"{'Trades':>8}"
        f"{'Win %':>9}"
        f"{'PF':>9}"
        f"{'Expect %':>11}"
        f"{'Avg %':>9}"
        f"{'Best %':>9}"
        f"{'Worst %':>10}"
        f"{'Rating':>14}"
    )

    print("-" * 92)

    for s in ranked_symbols:
        print(
            f"{s['symbol']:<10}"
            f"{s['trades']:>8}"
            f"{s['win_rate']:>8.1f}%"
            f"{s['profit_factor']:>9.2f}"
            f"{s['expectancy']:>11.2f}"
            f"{s['avg_return']:>9.2f}"
            f"{s['best']:>9.2f}"
            f"{s['worst']:>10.2f}"
            f"{s['rating']:>14}"
        )

    print("=" * 92)

def print_research_summary(stats):
    ranked = build_ranked_symbols(stats)

    strong = [s for s in ranked if s["rating"] == "STRONG"]
    good = [s for s in ranked if s["rating"] == "GOOD"]
    weak = [s for s in ranked if s["rating"] == "WEAK EDGE"]
    low = [s for s in ranked if s["rating"] == "LOW SAMPLE"]

    print()
    print("=" * 92)
    print("RESEARCH SUMMARY")
    print("=" * 92)

    print("\n🏆 TOP PERFORMING SYMBOLS")
    print("-" * 40)

    if strong:
        for s in strong:
            print(
                f"{s['symbol']:<10}"
                f" Expectancy: {s['expectancy']:>5.2f}%"
                f"   PF: {s['profit_factor']:>5.2f}"
            )
    else:
        print("None")

    print("\n👍 GOOD CANDIDATES")
    print("-" * 40)

    if good:
        for s in good:
            print(s["symbol"])
    else:
        print("None")

    print("\n⚠ NEEDS IMPROVEMENT")
    print("-" * 40)

    if weak:
        for s in weak:
            print(s["symbol"])
    else:
        print("None")

    print("\n📊 LOW SAMPLE SIZE")
    print("-" * 40)

    if low:
        for s in low:
            print(f"{s['symbol']} ({s['trades']} trades)")
    else:
        print("None")

    print("=" * 92)

def main():
    results = run_watchlist_backtest(
        min_tmqs=95,
        min_rvol=1.0,
        breakout_only=True,
        atr_multiplier=2.0,
        reward_multiplier=2.5,
        max_hold_days=10,
    )

    trades = results["trades"]
    stats = calculate_symbol_stats(trades)

    print_symbol_analysis(stats)
    print_research_summary(stats)


if __name__ == "__main__":
    main()