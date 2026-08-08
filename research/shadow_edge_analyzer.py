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



NUMERIC_FACTORS = [
    "rs_xic_20",
    "rs_xiu_20",
    "ma_close_vs_sma20_percent",
    "ma_close_vs_sma50_percent",
    "ma_close_vs_sma200_percent",
    "sector_strength_20",
    "gap_percent",
    "atr_percent",
]


def compare_numeric_factor(
    trades,
    field,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
    bucket_count=3,
):
    """
    Compare a numeric research factor using rank-based buckets.

    Missing and non-numeric values are excluded from the
    eligible baseline.

    The buckets are exploratory only. They do not change
    trading rules or establish an edge.
    """

    eligible = []

    for trade in trades:
        raw_value = str(
            trade.get(field, "")
        ).strip()

        if not raw_value:
            continue

        try:
            numeric_value = float(
                raw_value
            )
        except (TypeError, ValueError):
            continue

        eligible.append(
            (
                trade,
                numeric_value,
            )
        )

    eligible_trades = [
        trade
        for trade, _ in eligible
    ]

    eligible_baseline = (
        calculate_baseline_stats(
            eligible_trades
        )
    )

    missing_trade_count = (
        len(trades)
        - len(eligible_trades)
    )

    if not eligible:
        return {
            "factor": field,
            "total_trade_count": len(trades),
            "eligible_trade_count": 0,
            "missing_trade_count": (
                missing_trade_count
            ),
            "eligible_baseline": (
                eligible_baseline
            ),
            "groups": [],
        }

    sorted_eligible = sorted(
        eligible,
        key=lambda item: item[1],
    )

    actual_bucket_count = min(
        max(
            int(bucket_count),
            1,
        ),
        len(sorted_eligible),
    )

    if actual_bucket_count == 3:
        labels = [
            "LOW",
            "MIDDLE",
            "HIGH",
        ]
    else:
        labels = [
            f"BUCKET_{index + 1}"
            for index in range(
                actual_bucket_count
            )
        ]

    buckets = {
        label: []
        for label in labels
    }

    for rank, item in enumerate(
        sorted_eligible
    ):
        bucket_index = min(
            (
                rank
                * actual_bucket_count
            )
            // len(sorted_eligible),
            actual_bucket_count - 1,
        )

        label = labels[
            bucket_index
        ]

        buckets[label].append(
            item
        )

    group_results = []

    for label in labels:
        bucket_items = buckets[
            label
        ]

        if not bucket_items:
            continue

        bucket_trades = [
            trade
            for trade, _ in bucket_items
        ]

        bucket_values = [
            value
            for _, value in bucket_items
        ]

        group_stats = (
            calculate_baseline_stats(
                bucket_trades
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
                "value": label,
                "minimum_value": min(
                    bucket_values
                ),
                "maximum_value": max(
                    bucket_values
                ),
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



def collect_shadow_candidates(
    trades,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
):
    """
    Collect descriptive shadow candidates.

    A candidate is simply a group currently performing better
    than its eligible baseline.

    Candidates remain subject to their sample-size status and
    must never be interpreted as proven trading edges.
    """

    candidates = []

    categorical_results = (
        analyze_individual_factors(
            trades,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )
    )

    for result in categorical_results:
        baseline = result[
            "eligible_baseline"
        ]

        for group in result["groups"]:
            if (
                group["direction"]
                != "BETTER_THAN_BASELINE"
            ):
                continue

            stats = group["stats"]

            candidates.append(
                {
                    "factor_type": "CATEGORICAL",
                    "factor": result["factor"],
                    "value": group["value"],
                    "minimum_value": None,
                    "maximum_value": None,
                    "trade_count": stats[
                        "trade_count"
                    ],
                    "win_rate": stats[
                        "win_rate"
                    ],
                    "profit_factor": stats[
                        "profit_factor"
                    ],
                    "expectancy": stats[
                        "expectancy"
                    ],
                    "baseline_expectancy": (
                        baseline["expectancy"]
                    ),
                    "expectancy_delta": (
                        stats["expectancy"]
                        - baseline["expectancy"]
                    ),
                    "status": group[
                        "status"
                    ],
                    "direction": group[
                        "direction"
                    ],
                }
            )

    for factor in NUMERIC_FACTORS:
        result = compare_numeric_factor(
            trades,
            factor,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )

        baseline = result[
            "eligible_baseline"
        ]

        for group in result["groups"]:
            if (
                group["direction"]
                != "BETTER_THAN_BASELINE"
            ):
                continue

            stats = group["stats"]

            candidates.append(
                {
                    "factor_type": "NUMERIC",
                    "factor": factor,
                    "value": group["value"],
                    "minimum_value": group[
                        "minimum_value"
                    ],
                    "maximum_value": group[
                        "maximum_value"
                    ],
                    "trade_count": stats[
                        "trade_count"
                    ],
                    "win_rate": stats[
                        "win_rate"
                    ],
                    "profit_factor": stats[
                        "profit_factor"
                    ],
                    "expectancy": stats[
                        "expectancy"
                    ],
                    "baseline_expectancy": (
                        baseline["expectancy"]
                    ),
                    "expectancy_delta": (
                        stats["expectancy"]
                        - baseline["expectancy"]
                    ),
                    "status": group[
                        "status"
                    ],
                    "direction": group[
                        "direction"
                    ],
                }
            )

    candidates.sort(
        key=lambda candidate: (
            candidate["trade_count"],
            candidate["expectancy_delta"],
        ),
        reverse=True,
    )

    return candidates



def _numeric_bucket_member_indices(
    trades,
    field,
    bucket_count=3,
):
    """
    Return the journal row indices assigned to each numeric bucket.

    This mirrors the rank-based bucketing used by
    compare_numeric_factor().
    """

    eligible = []

    for index, trade in enumerate(trades):
        raw_value = str(
            trade.get(field, "")
        ).strip()

        if not raw_value:
            continue

        try:
            numeric_value = float(
                raw_value
            )
        except (TypeError, ValueError):
            continue

        eligible.append(
            (
                index,
                numeric_value,
            )
        )

    if not eligible:
        return {}

    eligible.sort(
        key=lambda item: item[1]
    )

    actual_bucket_count = min(
        max(
            int(bucket_count),
            1,
        ),
        len(eligible),
    )

    if actual_bucket_count == 3:
        labels = [
            "LOW",
            "MIDDLE",
            "HIGH",
        ]
    else:
        labels = [
            f"BUCKET_{index + 1}"
            for index in range(
                actual_bucket_count
            )
        ]

    buckets = {
        label: set()
        for label in labels
    }

    for rank, item in enumerate(
        eligible
    ):
        bucket_index = min(
            (
                rank
                * actual_bucket_count
            )
            // len(eligible),
            actual_bucket_count - 1,
        )

        label = labels[
            bucket_index
        ]

        row_index = item[0]

        buckets[label].add(
            row_index
        )

    return buckets


def collect_shadow_candidate_memberships(
    trades,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
):
    """
    Collect the journal-row membership of every
    better-than-baseline shadow candidate.
    """

    memberships = []

    categorical_results = (
        analyze_individual_factors(
            trades,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )
    )

    for result in categorical_results:
        factor = result["factor"]

        for group in result["groups"]:
            if (
                group["direction"]
                != "BETTER_THAN_BASELINE"
            ):
                continue

            value = group["value"]

            member_indices = {
                index
                for index, trade in enumerate(
                    trades
                )
                if (
                    str(
                        trade.get(
                            factor,
                            "",
                        )
                    ).strip()
                    == value
                )
            }

            memberships.append(
                {
                    "factor_type": (
                        "CATEGORICAL"
                    ),
                    "factor": factor,
                    "value": value,
                    "minimum_value": None,
                    "maximum_value": None,
                    "member_indices": (
                        member_indices
                    ),
                }
            )

    for factor in NUMERIC_FACTORS:
        result = compare_numeric_factor(
            trades,
            factor,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )

        buckets = (
            _numeric_bucket_member_indices(
                trades,
                factor,
            )
        )

        for group in result["groups"]:
            if (
                group["direction"]
                != "BETTER_THAN_BASELINE"
            ):
                continue

            value = group["value"]

            memberships.append(
                {
                    "factor_type": "NUMERIC",
                    "factor": factor,
                    "value": value,
                    "minimum_value": group[
                        "minimum_value"
                    ],
                    "maximum_value": group[
                        "maximum_value"
                    ],
                    "member_indices": set(
                        buckets.get(
                            value,
                            set(),
                        )
                    ),
                }
            )

    return memberships


def analyze_candidate_overlap(
    trades,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
    minimum_overlap_percent=66.0,
):
    """
    Detect duplicate, subset and highly overlapping candidates.

    This protects the research process from counting several
    descriptions of the same trades as independent evidence.
    """

    memberships = (
        collect_shadow_candidate_memberships(
            trades,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )
    )

    results = []

    for left_index in range(
        len(memberships)
    ):
        for right_index in range(
            left_index + 1,
            len(memberships),
        ):
            left = memberships[
                left_index
            ]

            right = memberships[
                right_index
            ]

            left_members = left[
                "member_indices"
            ]

            right_members = right[
                "member_indices"
            ]

            if (
                not left_members
                or not right_members
            ):
                continue

            shared = (
                left_members
                & right_members
            )

            if not shared:
                continue

            union = (
                left_members
                | right_members
            )

            left_overlap_percent = (
                len(shared)
                / len(left_members)
                * 100
            )

            right_overlap_percent = (
                len(shared)
                / len(right_members)
                * 100
            )

            smaller_overlap_percent = (
                len(shared)
                / min(
                    len(left_members),
                    len(right_members),
                )
                * 100
            )

            jaccard_percent = (
                len(shared)
                / len(union)
                * 100
            )

            if (
                left_members
                == right_members
            ):
                relationship = (
                    "EXACT_DUPLICATE"
                )

            elif (
                left_members
                < right_members
            ):
                relationship = (
                    "LEFT_SUBSET_OF_RIGHT"
                )

            elif (
                right_members
                < left_members
            ):
                relationship = (
                    "RIGHT_SUBSET_OF_LEFT"
                )

            elif (
                smaller_overlap_percent
                >= minimum_overlap_percent
            ):
                relationship = (
                    "HIGH_OVERLAP"
                )

            else:
                continue

            results.append(
                {
                    "left": left,
                    "right": right,
                    "relationship": (
                        relationship
                    ),
                    "shared_count": len(
                        shared
                    ),
                    "shared_indices": (
                        shared
                    ),
                    "left_count": len(
                        left_members
                    ),
                    "right_count": len(
                        right_members
                    ),
                    "left_overlap_percent": (
                        left_overlap_percent
                    ),
                    "right_overlap_percent": (
                        right_overlap_percent
                    ),
                    "smaller_overlap_percent": (
                        smaller_overlap_percent
                    ),
                    "jaccard_percent": (
                        jaccard_percent
                    ),
                }
            )

    relationship_priority = {
        "EXACT_DUPLICATE": 3,
        "LEFT_SUBSET_OF_RIGHT": 2,
        "RIGHT_SUBSET_OF_LEFT": 2,
        "HIGH_OVERLAP": 1,
    }

    results.sort(
        key=lambda result: (
            relationship_priority[
                result["relationship"]
            ],
            result[
                "smaller_overlap_percent"
            ],
            result["shared_count"],
        ),
        reverse=True,
    )

    return results



def analyze_candidate_cohort_concentration(
    trades,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
    concentration_threshold_percent=66.0,
):
    """
    Measure whether shadow candidates are concentrated in
    the same entry date or entry/exit trade cohort.

    High cohort concentration means the apparent candidate
    may reflect one market period rather than an independent
    and repeatable factor effect.
    """

    memberships = (
        collect_shadow_candidate_memberships(
            trades,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )
    )

    results = []

    for candidate in memberships:
        member_indices = candidate[
            "member_indices"
        ]

        entry_dates = {}
        entry_exit_cohorts = {}

        dated_trade_count = 0

        for index in member_indices:
            trade = trades[index]

            entry_date = str(
                trade.get(
                    "entry_date",
                    "",
                )
            ).strip()

            exit_date = str(
                trade.get(
                    "exit_date",
                    "",
                )
            ).strip()

            if not entry_date:
                continue

            dated_trade_count += 1

            entry_dates[entry_date] = (
                entry_dates.get(
                    entry_date,
                    0,
                )
                + 1
            )

            if exit_date:
                cohort = (
                    entry_date,
                    exit_date,
                )

                entry_exit_cohorts[
                    cohort
                ] = (
                    entry_exit_cohorts.get(
                        cohort,
                        0,
                    )
                    + 1
                )

        dominant_entry_date = None
        dominant_entry_count = 0

        if entry_dates:
            (
                dominant_entry_date,
                dominant_entry_count,
            ) = max(
                entry_dates.items(),
                key=lambda item: item[1],
            )

        dominant_cohort = None
        dominant_cohort_count = 0

        if entry_exit_cohorts:
            (
                dominant_cohort,
                dominant_cohort_count,
            ) = max(
                entry_exit_cohorts.items(),
                key=lambda item: item[1],
            )

        entry_concentration_percent = 0.0
        cohort_concentration_percent = 0.0

        if dated_trade_count > 0:
            entry_concentration_percent = (
                dominant_entry_count
                / dated_trade_count
                * 100
            )

            cohort_concentration_percent = (
                dominant_cohort_count
                / dated_trade_count
                * 100
            )

        if dated_trade_count < 2:
            concentration_status = (
                "INSUFFICIENT_COHORT_DATA"
            )

        elif (
            cohort_concentration_percent
            >= concentration_threshold_percent
        ):
            concentration_status = (
                "HIGH_ENTRY_EXIT_CONCENTRATION"
            )

        elif (
            entry_concentration_percent
            >= concentration_threshold_percent
        ):
            concentration_status = (
                "HIGH_ENTRY_DATE_CONCENTRATION"
            )

        else:
            concentration_status = (
                "DIVERSE_COHORTS"
            )

        results.append(
            {
                "factor_type": candidate[
                    "factor_type"
                ],
                "factor": candidate[
                    "factor"
                ],
                "value": candidate[
                    "value"
                ],
                "trade_count": len(
                    member_indices
                ),
                "dated_trade_count": (
                    dated_trade_count
                ),
                "dominant_entry_date": (
                    dominant_entry_date
                ),
                "dominant_entry_count": (
                    dominant_entry_count
                ),
                "entry_concentration_percent": (
                    entry_concentration_percent
                ),
                "dominant_entry_exit_cohort": (
                    dominant_cohort
                ),
                "dominant_cohort_count": (
                    dominant_cohort_count
                ),
                "cohort_concentration_percent": (
                    cohort_concentration_percent
                ),
                "concentration_status": (
                    concentration_status
                ),
            }
        )

    results.sort(
        key=lambda result: (
            result[
                "cohort_concentration_percent"
            ],
            result[
                "entry_concentration_percent"
            ],
            result["trade_count"],
        ),
        reverse=True,
    )

    return results



def _shadow_candidate_key(
    factor_type,
    factor,
    value,
):
    """
    Build a stable identifier for one shadow candidate.
    """

    return (
        str(factor_type),
        str(factor),
        str(value),
    )


def build_candidate_quality_gate(
    trades,
    minimum_sample_size=DEFAULT_MINIMUM_SAMPLE_SIZE,
    material_overlap_percent=66.0,
):
    """
    Combine candidate performance, overlap and cohort safeguards.

    High-overlap relationships are evaluated directionally.
    A broad candidate is not penalized merely because a much
    smaller candidate substantially overlaps it.

    This is research only. It does not modify trading rules.
    """

    candidates = collect_shadow_candidates(
        trades,
        minimum_sample_size=(
            minimum_sample_size
        ),
    )

    cohorts = (
        analyze_candidate_cohort_concentration(
            trades,
            minimum_sample_size=(
                minimum_sample_size
            ),
        )
    )

    overlaps = analyze_candidate_overlap(
        trades,
        minimum_sample_size=(
            minimum_sample_size
        ),
        minimum_overlap_percent=(
            material_overlap_percent
        ),
    )

    cohort_lookup = {}

    for cohort in cohorts:
        key = _shadow_candidate_key(
            cohort["factor_type"],
            cohort["factor"],
            cohort["value"],
        )

        cohort_lookup[key] = cohort

    overlap_flags = {}

    for candidate in candidates:
        key = _shadow_candidate_key(
            candidate["factor_type"],
            candidate["factor"],
            candidate["value"],
        )

        overlap_flags[key] = {
            "exact_duplicate_count": 0,
            "subset_of_other_count": 0,
            "contains_subset_count": 0,
            "high_overlap_count": 0,
            "material_high_overlap_count": 0,
        }

    for overlap in overlaps:
        left = overlap["left"]
        right = overlap["right"]

        left_key = _shadow_candidate_key(
            left["factor_type"],
            left["factor"],
            left["value"],
        )

        right_key = _shadow_candidate_key(
            right["factor_type"],
            right["factor"],
            right["value"],
        )

        relationship = overlap[
            "relationship"
        ]

        if (
            left_key not in overlap_flags
            or right_key not in overlap_flags
        ):
            continue

        if relationship == "EXACT_DUPLICATE":
            overlap_flags[
                left_key
            ][
                "exact_duplicate_count"
            ] += 1

            overlap_flags[
                right_key
            ][
                "exact_duplicate_count"
            ] += 1

        elif (
            relationship
            == "LEFT_SUBSET_OF_RIGHT"
        ):
            overlap_flags[
                left_key
            ][
                "subset_of_other_count"
            ] += 1

            overlap_flags[
                right_key
            ][
                "contains_subset_count"
            ] += 1

        elif (
            relationship
            == "RIGHT_SUBSET_OF_LEFT"
        ):
            overlap_flags[
                right_key
            ][
                "subset_of_other_count"
            ] += 1

            overlap_flags[
                left_key
            ][
                "contains_subset_count"
            ] += 1

        elif relationship == "HIGH_OVERLAP":
            overlap_flags[
                left_key
            ][
                "high_overlap_count"
            ] += 1

            overlap_flags[
                right_key
            ][
                "high_overlap_count"
            ] += 1

            if (
                overlap[
                    "left_overlap_percent"
                ]
                >= material_overlap_percent
            ):
                overlap_flags[
                    left_key
                ][
                    "material_high_overlap_count"
                ] += 1

            if (
                overlap[
                    "right_overlap_percent"
                ]
                >= material_overlap_percent
            ):
                overlap_flags[
                    right_key
                ][
                    "material_high_overlap_count"
                ] += 1

    results = []

    for candidate in candidates:
        key = _shadow_candidate_key(
            candidate["factor_type"],
            candidate["factor"],
            candidate["value"],
        )

        cohort = cohort_lookup.get(
            key,
            {},
        )

        flags = overlap_flags.get(
            key,
            {
                "exact_duplicate_count": 0,
                "subset_of_other_count": 0,
                "contains_subset_count": 0,
                "high_overlap_count": 0,
                "material_high_overlap_count": 0,
            },
        )

        concentration_status = (
            cohort.get(
                "concentration_status",
                "UNKNOWN",
            )
        )

        cohort_concentration_percent = (
            cohort.get(
                "cohort_concentration_percent",
                0.0,
            )
        )

        has_exact_duplicate = (
            flags[
                "exact_duplicate_count"
            ]
            > 0
        )

        is_subset_of_other = (
            flags[
                "subset_of_other_count"
            ]
            > 0
        )

        has_material_high_overlap = (
            flags[
                "material_high_overlap_count"
            ]
            > 0
        )

        has_high_concentration = (
            concentration_status
            in {
                "HIGH_ENTRY_EXIT_CONCENTRATION",
                "HIGH_ENTRY_DATE_CONCENTRATION",
            }
        )

        sample_status = candidate[
            "status"
        ]

        if (
            has_exact_duplicate
            or (
                has_high_concentration
                and is_subset_of_other
            )
        ):
            research_rating = (
                "HEAVILY_CONFOUNDED"
            )

        elif (
            has_high_concentration
            or is_subset_of_other
            or has_material_high_overlap
        ):
            if (
                sample_status
                == "PROMISING"
            ):
                research_rating = (
                    "PROMISING_BUT_CONFOUNDED"
                )
            else:
                research_rating = (
                    "CONFOUNDED_EARLY"
                )

        elif (
            sample_status
            == "PROMISING"
        ):
            research_rating = (
                "PROMISING_REVIEW"
            )

        else:
            research_rating = (
                "WATCH_ONLY"
            )

        results.append(
            {
                **candidate,
                "cohort_status": (
                    concentration_status
                ),
                "cohort_concentration_percent": (
                    cohort_concentration_percent
                ),
                "exact_duplicate_count": flags[
                    "exact_duplicate_count"
                ],
                "subset_of_other_count": flags[
                    "subset_of_other_count"
                ],
                "contains_subset_count": flags[
                    "contains_subset_count"
                ],
                "high_overlap_count": flags[
                    "high_overlap_count"
                ],
                "material_high_overlap_count": flags[
                    "material_high_overlap_count"
                ],
                "research_rating": (
                    research_rating
                ),
            }
        )

    rating_priority = {
        "PROMISING_REVIEW": 4,
        "WATCH_ONLY": 3,
        "PROMISING_BUT_CONFOUNDED": 2,
        "CONFOUNDED_EARLY": 1,
        "HEAVILY_CONFOUNDED": 0,
    }

    results.sort(
        key=lambda result: (
            rating_priority.get(
                result["research_rating"],
                -1,
            ),
            result["trade_count"],
            result["expectancy_delta"],
        ),
        reverse=True,
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

    for factor in NUMERIC_FACTORS:
        result = compare_numeric_factor(
            trades,
            factor,
        )

        print()
        print(
            f"NUMERIC FACTOR: {factor}"
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
                "No populated numeric data "
                "for this factor."
            )
            continue

        for group in result["groups"]:
            stats = group["stats"]

            value_range = (
                f"{group['minimum_value']:.2f}"
                " to "
                f"{group['maximum_value']:.2f}"
            )

            print(
                f"  {group['value']:<8}"
                f"{value_range:<22}"
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
