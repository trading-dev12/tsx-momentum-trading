"""
Research Dashboard

Professional research report for TSX Momentum strategy results.
"""

from collections import defaultdict


MIN_SAMPLE_SIZE = 3


def calculate_stats(trades):
    if not trades:
        return {
            "trades": 0,
            "win_rate": 0,
            "avg_return": 0,
            "profit_factor": 0,
            "expectancy": 0,
        }

    returns = [trade.get("return_pct", 0) for trade in trades]

    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]

    total_wins = sum(wins)
    total_losses = abs(sum(losses))

    return {
        "trades": len(trades),
        "win_rate": len(wins) / len(trades) * 100,
        "avg_return": sum(returns) / len(returns),
        "profit_factor": total_wins / total_losses if total_losses > 0 else 999,
        "expectancy": sum(returns) / len(returns),
    }


def print_table(title, rows, limit=None):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print(
        f"{'Label':<20}"
        f"{'Trades':>8}"
        f"{'Win %':>10}"
        f"{'PF':>10}"
        f"{'Avg %':>10}"
        f"{'Rating':>12}"
    )

    print("-" * 80)

    if limit:
        rows = rows[:limit]

    for label, trades in rows:
        stats = calculate_stats(trades)
        rating = rate_group(stats)

        print(
            f"{label:<20}"
            f"{stats['trades']:>8}"
            f"{stats['win_rate']:>10.2f}"
            f"{stats['profit_factor']:>10.2f}"
            f"{stats['avg_return']:>10.2f}"
            f"{rating:>12}"
        )


def rate_group(stats):
    if stats["trades"] < MIN_SAMPLE_SIZE:
        return "LOW SAMPLE"

    if stats["profit_factor"] >= 2 and stats["avg_return"] > 2:
        return "STRONG"

    if stats["profit_factor"] >= 1.3 and stats["avg_return"] > 0:
        return "GOOD"

    if stats["avg_return"] > 0:
        return "WEAK EDGE"

    return "AVOID"


def group_by_symbol(trades):
    groups = defaultdict(list)

    for trade in trades:
        groups[trade.get("symbol", "UNKNOWN")].append(trade)

    return sorted(
        groups.items(),
        key=lambda item: calculate_stats(item[1])["avg_return"],
        reverse=True,
    )


def group_by_exit_reason(trades):
    groups = defaultdict(list)

    for trade in trades:
        groups[trade.get("exit_reason", "UNKNOWN")].append(trade)

    return sorted(
        groups.items(),
        key=lambda item: calculate_stats(item[1])["avg_return"],
        reverse=True,
    )


def group_by_tmqs(trades):
    groups = defaultdict(list)

    for trade in trades:
        tmqs = int(trade.get("tmqs", 0))
        label = "TMQS 100" if tmqs >= 100 else "TMQS 95-99"
        groups[label].append(trade)

    return sorted(
        groups.items(),
        key=lambda item: calculate_stats(item[1])["avg_return"],
        reverse=True,
    )


def group_by_rvol(trades):
    groups = defaultdict(list)

    for trade in trades:
        rvol = round(trade.get("rvol", 0))
        label = f"RVOL {rvol}"
        groups[label].append(trade)

    return sorted(
        groups.items(),
        key=lambda item: calculate_stats(item[1])["avg_return"],
        reverse=True,
    )


def group_by_hold_days(trades):
    groups = defaultdict(list)

    for trade in trades:
        label = f"{trade.get('hold_days', 0)} days"
        groups[label].append(trade)

    return sorted(
        groups.items(),
        key=lambda item: calculate_stats(item[1])["avg_return"],
        reverse=True,
    )


def run_dashboard(trades):
    print("\n" + "#" * 80)
    print("TSX MOMENTUM PRO - PROFESSIONAL RESEARCH DASHBOARD")
    print("#" * 80)

    print_table("TOP 15 STOCKS BY AVERAGE RETURN", group_by_symbol(trades), limit=15)

    bottom_stocks = list(reversed(group_by_symbol(trades)))
    print_table("BOTTOM 15 STOCKS BY AVERAGE RETURN", bottom_stocks, limit=15)

    print_table("TMQS PERFORMANCE", group_by_tmqs(trades))
    print_table("RVOL PERFORMANCE", group_by_rvol(trades))
    print_table("EXIT REASON PERFORMANCE", group_by_exit_reason(trades))
    print_table("HOLDING PERIOD PERFORMANCE", group_by_hold_days(trades))