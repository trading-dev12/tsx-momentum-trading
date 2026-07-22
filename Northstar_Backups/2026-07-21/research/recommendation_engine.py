"""
Strategy Recommendation Engine

Automatically identifies the strongest filters
from historical research.
"""


def recommend_tmqs(trades):
    high = [
        trade
        for trade in trades
        if trade.get("tmqs", 0) >= 100
    ]

    low = [
        trade
        for trade in trades
        if trade.get("tmqs", 0) < 100
    ]

    high_avg = (
        sum(trade["return_pct"] for trade in high) / len(high)
        if high
        else 0
    )

    low_avg = (
        sum(trade["return_pct"] for trade in low) / len(low)
        if low
        else 0
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
        returns = buckets[bucket]
        average_return = sum(returns) / len(returns)

        print(
            f"RVOL {bucket:<3}"
            f"{len(returns):>6} trades"
            f"{average_return:>10.2f}%"
        )

        if (
            len(returns) >= 5
            and average_return > best_avg
        ):
            best_avg = average_return
            best_bucket = bucket

    if best_bucket is not None:
        print()
        print(
            f"✓ Recommendation: Prefer RVOL around "
            f"{best_bucket}"
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

        average_return = sum(returns) / len(returns)

        averages.append(
            (
                symbol,
                len(returns),
                average_return,
            )
        )

    preferred_stocks = sorted(
        [
            result
            for result in averages
            if result[2] > 0
        ],
        key=lambda result: result[2],
        reverse=True,
    )

    avoid_stocks = sorted(
        [
            result
            for result in averages
            if result[2] < 0
        ],
        key=lambda result: result[2],
    )

    print("\nPreferred Stocks")
    print("-" * 60)

    if preferred_stocks:
        for (
            symbol,
            trade_count,
            average_return,
        ) in preferred_stocks[:10]:
            print(
                f"{symbol:<10}"
                f"{trade_count:>5} trades"
                f"{average_return:>10.2f}%"
            )
    else:
        print(
            "No stocks currently meet "
            "the preferred criteria."
        )

    print("\nAvoid Stocks")
    print("-" * 60)

    if avoid_stocks:
        for (
            symbol,
            trade_count,
            average_return,
        ) in avoid_stocks[:10]:
            print(
                f"{symbol:<10}"
                f"{trade_count:>5} trades"
                f"{average_return:>10.2f}%"
            )
    else:
        print(
            "No stocks with at least 5 trades "
            "currently have a negative average return."
        )


def run_recommendation_engine(trades):
    print("\n")
    print("#" * 70)
    print("STRATEGY RECOMMENDATION ENGINE")
    print("#" * 70)

    recommend_tmqs(trades)
    recommend_rvol(trades)
    recommend_stocks(trades)