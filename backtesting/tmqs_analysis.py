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


def print_score_analysis(title, scores):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    if not scores:
        print("No scores found.")
        return

    buckets = Counter(get_bucket(score) for score in scores)

    print("\nTMQS Score Buckets:")
    for label in [
        "0-9",
        "10-19",
        "20-29",
        "30-39",
        "40-49",
        "50-59",
        "60-69",
        "70-79",
        "80-89",
        "90-99",
        "100",
    ]:
        print(f"{label:>6}: {buckets[label]}")

    print("\nRounded TMQS Scores:")
    rounded_scores = Counter(round(score) for score in scores)

    for score in range(int(min(scores)), int(max(scores)) + 1):
        if rounded_scores[score] > 0:
            print(f"{score:>6}: {rounded_scores[score]}")

    sorted_scores = sorted(scores)
    total = len(sorted_scores)
    average = sum(sorted_scores) / total
    median = sorted_scores[total // 2]

    q1 = sorted_scores[total // 4]
    q3 = sorted_scores[(total * 3) // 4]

    print("\nSummary:")
    print(f"Total setups analyzed : {total}")
    print(f"Average TMQS          : {average:.2f}")
    print(f"Median TMQS           : {median}")
    print(f"Lowest TMQS           : {min(sorted_scores)}")
    print(f"Highest TMQS          : {max(sorted_scores)}")
    print(f"Q1 TMQS               : {q1}")
    print(f"Q3 TMQS               : {q3}")


def main():
    print("=" * 70)
    print("TMQS DISTRIBUTION ANALYSIS")
    print("=" * 70)

    folder_path = "data/historical"

    all_scores = []
    ready_scores = []
    decisions = Counter()
    breakouts = Counter()
    ready_breakouts = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".csv"):
            continue

        file_path = os.path.join(folder_path, filename)
        rows = load_historical_csv(file_path)

        for index in range(1, len(rows)):
            signal = evaluate_historical_setup(rows[index], rows[index - 1])

            tmqs = signal["tmqs"]
            decision = signal["decision"]
            breakout = signal["breakout"]

            all_scores.append(tmqs)
            decisions[decision] += 1
            breakouts[breakout] += 1

            if decision == "READY":
                ready_scores.append(tmqs)
                ready_breakouts[breakout] += 1

    print_score_analysis("ALL SETUPS", all_scores)
    print_score_analysis("READY TRADES ONLY", ready_scores)

    print("\nDecision Counts:")
    for decision, count in decisions.items():
        print(f"{decision:>8}: {count}")

    print("\nBreakout Counts - All Setups:")
    for breakout, count in breakouts.items():
        print(f"{breakout:>18}: {count}")

    print("\nBreakout Counts - READY Trades Only:")
    for breakout, count in ready_breakouts.items():
        print(f"{breakout:>18}: {count}")


if __name__ == "__main__":
    main()