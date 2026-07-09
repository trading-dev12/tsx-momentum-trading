"""
Stock Rankings

Ranks every stock in the research universe using
historical backtest results.
"""

from collections import defaultdict


def rank_stocks(trades):
    stats = defaultdict(
        lambda: {
            "trades": 0,
            "wins": 0,
            "returns": [],
            "winning_returns": [],
            "losing_returns": [],
        }
    )

    for trade in trades:
        symbol = trade["symbol"]
        ret = trade.get("return_percent", trade.get("return_pct", trade.get("return", 0)))

        s = stats[symbol]

        s["trades"] += 1
        s["returns"].append(ret)

        if ret > 0:
            s["wins"] += 1
            s["winning_returns"].append(ret)
        else:
            s["losing_returns"].append(ret)

    print("\n")
    print("=" * 72)
    print("STOCK RANKINGS")
    print("=" * 72)

    print(
        f'{"Symbol":<10}'
        f'{"Trades":>8}'
        f'{"Win%":>10}'
        f'{"Avg":>10}'
    )

    print("-" * 72)

    for symbol in sorted(stats):

        s = stats[symbol]

        win_rate = (
            s["wins"] / s["trades"] * 100
            if s["trades"] > 0
            else 0
        )

        avg_return = sum(s["returns"]) / len(s["returns"])

        print(
            f"{symbol:<10}"
            f"{s['trades']:>8}"
            f"{win_rate:>9.1f}%"
            f"{avg_return:>9.2f}%"
        )