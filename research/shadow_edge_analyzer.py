"""
Northstar Quant
Shadow Edge Analyzer

Read-only research module for evaluating completed paper trades.

This module must never modify trading rules, signals, positions,
pending trades, portfolios, or journals.
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_MINIMUM_SAMPLE_SIZE = 30

CATEGORICAL_FACTORS = [
    "market_regime",
    "ma_trend_alignment",
    "gap_bucket",
    "volatility_regime",
]


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_completed_trades(file_path):
    """
    Load completed trades from a paper-trade journal.

    The journal is read only.
    """

    path = Path(file_path)

    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def calculate_baseline_stats(trades):
    """
    Calculate baseline performance statistics for a trade sample.
    """

    completed = []

    for trade in trades:
        profit_loss = _to_float(
            trade.get("profit_loss")
        )

        profit_loss_percent = _to_float(
            trade.get("profit_loss_percent")
        )

        completed.append(
            {
                "profit_loss": profit_loss,
                "profit_loss_percent": (
                    profit_loss_percent
                ),
            }
        )

    trade_count = len(completed)

    if trade_count == 0:
        return {
            "trade_count": 0,
            "wins": 0,
            "losses": 0,
            "breakeven": 0,
            "win_rate": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": None,
            "total_profit_loss": 0.0,
            "expectancy": 0.0,
            "average_gain": 0.0,
            "average_loss": 0.0,
            "average_return_percent": 0.0,
            "sample_status": "NO_DATA",
        }

    wins = [
        trade
        for trade in completed
        if trade["profit_loss"] > 0
    ]

    losses = [
        trade
        for trade in completed
        if trade["profit_loss"] < 0
    ]

    breakeven = [
        trade
        for trade in completed
        if trade["profit_loss"] == 0
    ]

    gross_profit = sum(
        trade["profit_loss"]
        for trade in wins
    )

    gross_loss = abs(
        sum(
            trade["profit_loss"]
            for trade in losses
        )
    )

    total_profit_loss = sum(
        trade["profit_loss"]
        for trade in completed
    )

    profit_factor = None

    if gross_loss > 0:
        profit_factor = (
            gross_profit / gross_loss
        )

    win_rate = (
        len(wins) / trade_count
    ) * 100

    expectancy = (
        total_profit_loss / trade_count
    )

    average_gain = (
        gross_profit / len(wins)
        if wins
        else 0.0
    )

    average_loss = (
        gross_loss / len(losses)
        if losses
        else 0.0
    )

    average_return_percent = (
        sum(
            trade["profit_loss_percent"]
            for trade in completed
        )
        / trade_count
    )

    if trade_count >= 200:
        sample_status = "VALIDATION_SAMPLE"
    elif trade_count >= 100:
        sample_status = "MATURING"
    elif trade_count >= 30:
        sample_status = "DEVELOPING"
    else:
        sample_status = "VERY_EARLY"

    return {
        "trade_count": trade_count,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakeven),
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "total_profit_loss": total_profit_loss,
        "expectancy": expectancy,
        "average_gain": average_gain,
        "average_loss": average_loss,
        "average_return_percent": (
            average_return_percent
        ),
        "sample_status": sample_status,
    }


def analyze_journal(file_path):
    """
    Load one journal and return its baseline statistics.
    """

    trades = load_completed_trades(
        file_path
    )

    return calculate_baseline_stats(
        trades
    )


def _profit_factor_score(stats):
    """
    Convert Profit Factor into a comparable numeric value.
    """

    profit_factor = stats.get(
        "profit_factor"
    )

    if profit_factor is not None:
        return profit_factor

    if stats.get("gross_profit", 0.0) > 0:
        return float("inf")

    return 0.0


def compare_stats_to_baseline(
    baseline_stats,
    group_stats,
):
    """
    Describe whether a group is performing better or worse
    than its eligible baseline.

    This is descriptive only and does not prove an edge.
    """

    baseline_pf = _profit_factor_score(
        baseline_stats
    )

    group_pf = _profit_factor_score(
        group_stats
    )

    baseline_expectancy = baseline_stats[
        "expectancy"
    ]

    group_expectancy = group_stats[
        "expectancy"
    ]

    if (
        group_pf > baseline_pf
        and group_expectancy > baseline_expectancy
    ):
        return "BETTER_THAN_BASELINE"

    if (
        group_pf < baseline_pf
        and group_expectancy < baseline_expectancy
    ):
        return "WORSE_THAN_BASELINE"

    return "MIXED"


def classify_shadow_result(
    baseline_stats,
    group_stats,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
):
    """
    Apply the minimum-sample safeguard.

    No group can be called PROMISING until it contains at least
    the configured minimum number of completed trades.
    """

    direction = compare_stats_to_baseline(
        baseline_stats,
        group_stats,
    )

    if (
        group_stats["trade_count"]
        < minimum_sample_size
    ):
        return {
            "status": "INSUFFICIENT_DATA",
            "direction": direction,
        }

    if direction == "BETTER_THAN_BASELINE":
        return {
            "status": "PROMISING",
            "direction": direction,
        }

    return {
        "status": "NO_IMPROVEMENT",
        "direction": direction,
    }


def compare_categorical_factor(
    trades,
    field,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
):
    """
    Compare each populated category of one research factor.

    Trades missing the requested factor are excluded from that
    factor's baseline so missing historical enrichment cannot
    distort the comparison.
    """

    eligible_trades = [
        trade
        for trade in trades
        if str(
            trade.get(field, "")
        ).strip()
    ]

    missing_trade_count = (
        len(trades) - len(eligible_trades)
    )

    eligible_baseline = (
        calculate_baseline_stats(
            eligible_trades
        )
    )

    groups = defaultdict(list)

    for trade in eligible_trades:
        value = str(
            trade.get(field, "")
        ).strip()

        groups[value].append(
            trade
        )

    group_results = []

    for value in sorted(groups):
        group_stats = (
            calculate_baseline_stats(
                groups[value]
            )
        )

        classification = (
            classify_shadow_result(
                eligible_baseline,
                group_stats,
                minimum_sample_size=(
                    minimum_sample_size
                ),
            )
        )

        group_results.append(
            {
                "value": value,
                "stats": group_stats,
                "status": classification[
                    "status"
                ],
                "direction": classification[
                    "direction"
                ],
            }
        )

    return {
        "factor": field,
        "total_trade_count": len(trades),
        "eligible_trade_count": len(
            eligible_trades
        ),
        "missing_trade_count": (
            missing_trade_count
        ),
        "eligible_baseline": (
            eligible_baseline
        ),
        "groups": group_results,
    }


def analyze_individual_factors(
    trades,
    factors=None,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
):
    """
    Analyze individual categorical research factors.
    """

    if factors is None:
        factors = CATEGORICAL_FACTORS

    results = []

    for factor in factors:
        results.append(
            compare_categorical_factor(
                trades,
                factor,
                minimum_sample_size=(
                    minimum_sample_size
                ),
            )
        )

    return results


def _format_profit_factor(stats):
    profit_factor = stats.get(
        "profit_factor"
    )

    if profit_factor is None:
        if stats.get(
            "gross_profit",
            0.0,
        ) > 0:
            return "INF"

        return "--"

    return f"{profit_factor:.2f}"


def print_shadow_report(file_path):
    """
    Print the current read-only Shadow Edge Analyzer report.
    """

    trades = load_completed_trades(
        file_path
    )

    baseline = calculate_baseline_stats(
        trades
    )

    print()
    print("=" * 78)
    print(
        "NORTHSTAR QUANT - SHADOW EDGE ANALYZER"
    )
    print("=" * 78)

    print()
    print("FULL JOURNAL BASELINE")
    print("-" * 78)

    print(
        f"Trades: {baseline['trade_count']} | "
        f"Win Rate: {baseline['win_rate']:.2f}% | "
        f"PF: {_format_profit_factor(baseline)} | "
        f"Expectancy: "
        f"${baseline['expectancy']:.2f} | "
        f"Sample: {baseline['sample_status']}"
    )

    factor_results = (
        analyze_individual_factors(
            trades
        )
    )

    for result in factor_results:
        print()
        print(
            f"FACTOR: {result['factor']}"
        )
        print("-" * 78)

        print(
            "Coverage: "
            f"{result['eligible_trade_count']}/"
            f"{result['total_trade_count']} "
            "trades | "
            f"Missing: "
            f"{result['missing_trade_count']}"
        )

        eligible_baseline = result[
            "eligible_baseline"
        ]

        print(
            "Eligible baseline: "
            f"PF "
            f"{_format_profit_factor(eligible_baseline)} | "
            f"Expectancy "
            f"${eligible_baseline['expectancy']:.2f}"
        )

        if not result["groups"]:
            print(
                "No populated data for this factor."
            )
            continue

        for group in result["groups"]:
            stats = group["stats"]

            print(
                f"  {group['value']:<24}"
                f"Trades {stats['trade_count']:>3} | "
                f"Win {stats['win_rate']:>6.2f}% | "
                f"PF "
                f"{_format_profit_factor(stats):>5} | "
                f"Exp ${stats['expectancy']:>7.2f} | "
                f"{group['status']} | "
                f"{group['direction']}"
            )

    print()
    print(
        "Research only. No trading rules "
        "were modified."
    )


def main():
    file_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "paper_trade_journal.csv"
    )

    print_shadow_report(
        file_path
    )


if __name__ == "__main__":
    main()
