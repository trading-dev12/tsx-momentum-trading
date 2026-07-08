"""
TMQS distribution analysis tool.
"""

import os
from collections import Counter

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup


def get_bucket(score):
    if score >= 100:
        return "100"
    bucket_start = int(score // 10) * 10
    bucket_end = bucket_start + 9
    return f"{bucket_start}-{bucket_end}"


def main():
    print("=" * 70)
    print("TMQS DISTRIBUTION ANALYSIS")
    print("=" * 70)

    folder_path = "data/historical"

    scores = []
    decisions = Counter()
    breakouts = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".csv"):
            continue

        symbol = filename.replace(".csv", "")
        file_path = os.path.join(folder_path, filename)
        rows = load_historical_csv(file_path)

        for index in range(1, len(rows)):
            signal = evaluate_historical_setup(rows[index], rows[index - 1])

            scores.append(signal["tmqs"])
            decisions[signal["decision"]] += 1
            breakouts[signal["breakout"]] += 1

    buckets = Counter(get_bucket(score) for score in scores)

    print("\nTMQS Score Buckets:")
    for label in ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59",
                  "60-69", "70-79", "80-89", "90-99", "100"]:
        print(f"{label:>6}: {buckets[label]}")

    print("\nDecision Counts:")
    for decision, count in decisions.items():
        print(f"{decision:>8}: {count}")

    print("\nBreakout Counts:")
    for breakout, count in breakouts.items():
        print(f"{breakout:>18}: {count}")

    if scores:
        sorted_scores = sorted(scores)
        average = sum(scores) / len(scores)
        median = sorted_scores[len(sorted_scores) // 2]

        print("\nSummary:")
        print(f"Total setups analyzed : {len(scores)}")
        print(f"Average TMQS          : {average:.2f}")
        print(f"Median TMQS           : {median}")
        print(f"Lowest TMQS           : {min(scores)}")
        print(f"Highest TMQS          : {max(scores)}")


if __name__ == "__main__":
    main()