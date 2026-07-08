"""
Profiles the highest quality historical trades.
"""

from collections import Counter

from backtesting.backtester import run_watchlist_backtest


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def average(values):
    if not values:
        return 0
    return sum(values) / len(values)


def main():

    print_section("TSX MOMENTUM PRO - TRADE PROFILE")

    trades, stats = run_watchlist_backtest(
        min_tmqs=95,
        min_rvol=1.0,
        breakout_only=True,
        atr_multiplier=2.0,
        reward_multiplier=2.5,
        max_hold_days=10,
        show_report=False,
        save_log=False,
        verbose=False,
    )

    wins = [t for t in trades if t["profit_loss_percent"] > 0]
    losses = [t for t in trades if t["profit_loss_percent"] <= 0]

    print(f"\nTrades Analyzed : {len(trades)}")
    print(f"Winners         : {len(wins)}")
    print(f"Losers          : {len(losses)}")

    print_section("OVERALL PERFORMANCE")

    print(f"Return          : {stats['total_return']:.2f}%")
    print(f"Win Rate        : {stats['win_rate']:.2f}%")
    print(f"Profit Factor   : {stats['profit_factor']:.2f}")
    print(f"Expectancy      : {stats['expectancy']:.2f}%")
    print(f"Max Drawdown    : {stats['max_drawdown']:.2f}%")

    print_section("EXIT REASONS")

    exit_counts = Counter()

    for trade in trades:
        exit_counts[trade["exit_reason"]] += 1

    for reason, count in exit_counts.items():
        print(f"{reason:<25}: {count}")

    print_section("HOLDING PERIOD")

    holds = [trade["hold_days"] for trade in trades]

    print(f"Average Hold    : {average(holds):.2f} days")
    print(f"Shortest Hold   : {min(holds)} days")
    print(f"Longest Hold    : {max(holds)} days")

    print_section("WINNER / LOSER PROFILE")

    winner_returns = [trade["profit_loss_percent"] for trade in wins]
    loser_returns = [trade["profit_loss_percent"] for trade in losses]

    print(f"Average Winner  : {average(winner_returns):.2f}%")
    print(f"Average Loser   : {average(loser_returns):.2f}%")

    print_section("SETUP QUALITY PROFILE")

    tmqs = [trade["tmqs"] for trade in trades]
    rvol = [trade["rvol"] for trade in trades]

    print(f"Average TMQS    : {average(tmqs):.2f}")
    print(f"Average RVOL    : {average(rvol):.2f}")
    print(f"Lowest RVOL     : {min(rvol):.2f}")
    print(f"Highest RVOL    : {max(rvol):.2f}")

    print_section("BREAKOUT PROFILE")

    breakout_counts = Counter()

    for trade in trades:
        breakout_counts[trade["breakout"]] += 1

    for breakout, count in breakout_counts.items():
        print(f"{breakout:<20}: {count}")

    print_section("TOP 10 WINNERS")

    top_winners = sorted(
        trades,
        key=lambda t: t["profit_loss_percent"],
        reverse=True,
    )[:10]

    for trade in top_winners:
        print(
            f"{trade['symbol']:<8} | "
            f"{trade['entry_date']} -> {trade['exit_date']} | "
            f"{trade['profit_loss_percent']:.2f}% | "
            f"TMQS {trade['tmqs']:.2f} | "
            f"RVOL {trade['rvol']:.2f} | "
            f"{trade['exit_reason']}"
        )

    print_section("TOP 10 LOSERS")

    top_losers = sorted(
        trades,
        key=lambda t: t["profit_loss_percent"],
    )[:10]

    for trade in top_losers:
        print(
            f"{trade['symbol']:<8} | "
            f"{trade['entry_date']} -> {trade['exit_date']} | "
            f"{trade['profit_loss_percent']:.2f}% | "
            f"TMQS {trade['tmqs']:.2f} | "
            f"RVOL {trade['rvol']:.2f} | "
            f"{trade['exit_reason']}"
        )

    print_section("PERFORMANCE BY SYMBOL")

    symbol_stats = {}

    for trade in trades:
        symbol = trade["symbol"]
        result = trade["profit_loss_percent"]

        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                "trades": 0,
                "wins": 0,
                "returns": [],
                "winning_returns": [],
                "losing_returns": [],
                "best": -999,
                "worst": 999,
            }

        s = symbol_stats[symbol]

        s["trades"] += 1
        s["returns"].append(result)

        if result > 0:
            s["wins"] += 1
            s["winning_returns"].append(result)
        else:
            s["losing_returns"].append(result)

        s["best"] = max(s["best"], result)
        s["worst"] = min(s["worst"], result)

    print(
        f"{'Symbol':<10}"
        f"{'Trades':>8}"
        f"{'Win %':>10}"
        f"{'PF':>8}"
        f"{'Expect':>10}"
        f"{'Avg %':>10}"
        f"{'Best %':>10}"
        f"{'Worst %':>10}"
        f"{'Rating':>12}"
    )

    print("-" * 88)

    for symbol, s in sorted(
        symbol_stats.items(),
        key=lambda item: average(item[1]["returns"]),
        reverse=True,
    ):
        avg_return = average(s["returns"])
        win_rate = s["wins"] / s["trades"] * 100

        total_wins = sum(s["winning_returns"])
        total_losses = abs(sum(s["losing_returns"]))

        profit_factor = (
            total_wins / total_losses
            if total_losses > 0
            else 999
        )

        expectancy = avg_return

        if s["trades"] < 5:
            rating = "LOW SAMPLE"
        elif profit_factor >= 2 and expectancy > 2:
            rating = "STRONG"
        elif profit_factor >= 1.3 and expectancy > 0:
            rating = "GOOD"
        elif expectancy > 0:
            rating = "WEAK EDGE"
        else:
            rating = "AVOID"

        print(
            f"{symbol:<10}"
            f"{s['trades']:>8}"
            f"{win_rate:>9.1f}%"
            f"{profit_factor:>8.2f}"
            f"{expectancy:>9.2f}%"
            f"{avg_return:>9.2f}%"
            f"{s['best']:>9.2f}%"
            f"{s['worst']:>9.2f}%"
            f"{rating:>12}"
        )


if __name__ == "__main__":
    main()