"""
Edge Analyzer

Analyzes historical trades to identify where the strategy has the strongest edge.
"""

from collections import defaultdict


RETURN_FIELD = "return_pct"


def analyze_edge(trades):
    print("\n" + "=" * 70)
    print("TSX MOMENTUM PRO - EDGE ANALYZER")
    print("=" * 70)

    print(f"\nTrades Loaded: {len(trades)}")

    if not trades:
        print("No trades to analyze.")
        return

    analyze_tmqs(trades)
    analyze_rvol(trades)
    analyze_breakouts(trades)


def calculate_stats(group):
    returns = [trade.get(RETURN_FIELD, 0) for trade in group]

    total = len(returns)
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    win_rate = (len(wins) / total) * 100 if total > 0 else 0
    avg_return = sum(returns) / total if total > 0 else 0

    total_wins = sum(wins)
    total_losses = abs(sum(losses))

    profit_factor = total_wins / total_losses if total_losses > 0 else 999

    return {
        "trades": total,
        "win_rate": win_rate,
        "avg_return": avg_return,
        "profit_factor": profit_factor,
    }


def print_stats(label, group):
    stats = calculate_stats(group)

    print(
        f"{label:<20}"
        f"{stats['trades']:>6} trades "
        f"Win {stats['win_rate']:>6.2f}% "
        f"PF {stats['profit_factor']:>6.2f} "
        f"Avg {stats['avg_return']:>7.2f}%"
    )


def analyze_tmqs(trades):
    print("\nTMQS ANALYSIS")
    print("-" * 70)

    buckets = defaultdict(list)

    for trade in trades:
        score = trade.get("tmqs", 0)
        bucket = int(score // 5) * 5
        buckets[bucket].append(trade)

    for bucket in sorted(buckets):
        label = f"TMQS {bucket}-{bucket + 4}"
        print_stats(label, buckets[bucket])


def analyze_rvol(trades):
    print("\nRVOL ANALYSIS")
    print("-" * 70)

    buckets = defaultdict(list)

    for trade in trades:
        rvol = trade.get("rvol", 0)
        bucket = round(rvol)
        buckets[bucket].append(trade)

    for bucket in sorted(buckets):
        label = f"RVOL {bucket}"
        print_stats(label, buckets[bucket])


def analyze_breakouts(trades):
    print("\nBREAKOUT ANALYSIS")
    print("-" * 70)

    groups = defaultdict(list)

    for trade in trades:
        breakout = trade.get("breakout", "UNKNOWN")
        groups[breakout].append(trade)

    for breakout in sorted(groups):
        print_stats(breakout, groups[breakout])