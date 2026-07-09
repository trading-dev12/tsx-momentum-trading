"""
Strategy Recommendation Engine

Automatically identifies the strongest filters
from historical research.
"""


def recommend_tmqs(trades):
    high = [t for t in trades if t.get("tmqs", 0) >= 100]
    low = [t for t in trades if t.get("tmqs", 0) < 100]

    high_avg = (
        sum(t["return_pct"] for t in high) / len(high)
        if high else 0
    )

    low_avg = (
        sum(t["return_pct"] for t in low) / len(low)
        if low else 0
    )

    print("\nTMQS Recommendation")
    print("-" * 60)

    print(f"TMQS >=100 : {high_avg:.2f}%")
    print(f"TMQS <100  : {low_avg:.2f}%")

    if high_avg > low_avg:
        print("✓ Recommendation: Trade TMQS 100+ setups.")
    else:
        print("✓ Recommendation: Current TMQS filter needs review.")


def recommend_rvol(trades):
    buckets = {}

    for trade in trades:
        bucket = round(trade.get("rvol", 0))
        buckets.setdefault(bucket, [])
        buckets[bucket].append(trade["return_pct"])

    print("\nRVOL Recommendation")
    print("-" * 60)

    best_bucket = None
    best_avg = -999

    for bucket in sorted(buckets):

        avg = sum(buckets[bucket]) / len(buckets[bucket])

        print(
            f"RVOL {bucket:<3}"
            f"{len(buckets[bucket]):>6} trades"
            f"{avg:>10.2f}%"
        )

        if len(buckets[bucket]) >= 5 and avg > best_avg:
            best_avg = avg
            best_bucket = bucket

    if best_bucket is not None:
        print()
        print(
            f"✓ Recommendation: Prefer RVOL around {best_bucket}"
        )


def recommend_stocks(trades):

    groups = {}

    for trade in trades:
        symbol = trade["symbol"]

        groups.setdefault(symbol, [])
        groups[symbol].append(trade["return_pct"])

    averages = []

    for symbol, returns in groups.items():

        if len(returns) < 5:
            continue

        averages.append(
            (
                symbol,
                len(returns),
                sum(returns) / len(returns),
            )
        )

    averages.sort(key=lambda x: x[2], reverse=True)

    print("\nPreferred Stocks")
    print("-" * 60)

    for symbol, trades, avg in averages[:10]:
        print(f"{symbol:<10}{trades:>5} trades{avg:>10.2f}%")

    print("\nAvoid Stocks")
    print("-" * 60)

    for symbol, trades, avg in averages[-10:]:
        print(f"{symbol:<10}{trades:>5} trades{avg:>10.2f}%")


def run_recommendation_engine(trades):

    print("\n")
    print("#" * 70)
    print("STRATEGY RECOMMENDATION ENGINE")
    print("#" * 70)

    recommend_tmqs(trades)
    recommend_rvol(trades)
    recommend_stocks(trades)