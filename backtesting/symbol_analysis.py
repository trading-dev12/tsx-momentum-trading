"""
Symbol-level performance analysis.

This tool evaluates how each stock performs across all completed trades.
"""

from collections import defaultdict


def analyze_symbols(trades):
    stats = defaultdict(lambda: {
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "total_return": 0,
        "winner_return": 0,
        "loser_return": 0,
    })

    for trade in trades:

        symbol = trade["symbol"]
        result = trade["percent_return"]

        s = stats[symbol]

        s["trades"] += 1
        s["total_return"] += result

        if result > 0:
            s["wins"] += 1
            s["winner_return"] += result
        else:
            s["losses"] += 1
            s["loser_return"] += result

    print()
    print("=" * 70)
    print("SYMBOL PERFORMANCE")
    print("=" * 70)
    print()

    header = (
        f'{"Symbol":8}'
        f'{"Trades":>8}'
        f'{"Win %":>10}'
        f'{"Avg %":>10}'
        f'{"Avg Win":>12}'
        f'{"Avg Loss":>12}'
    )

    print(header)
    print("-" * len(header))

    sorted_symbols = sorted(
        stats.items(),
        key=lambda x: x[1]["total_return"],
        reverse=True,
    )

    for symbol, s in sorted_symbols:

        win_rate = (
            s["wins"] / s["trades"] * 100
            if s["trades"] > 0
            else 0
        )

        avg_return = s["total_return"] / s["trades"]

        avg_win = (
            s["winner_return"] / s["wins"]
            if s["wins"] > 0
            else 0
        )

        avg_loss = (
            s["loser_return"] / s["losses"]
            if s["losses"] > 0
            else 0
        )

        print(
            f"{symbol:8}"
            f"{s['trades']:>8}"
            f"{win_rate:>9.1f}%"
            f"{avg_return:>9.2f}%"
            f"{avg_win:>11.2f}%"
            f"{avg_loss:>11.2f}%"
        )