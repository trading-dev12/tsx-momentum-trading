"""
Northstar Quant
Shadow Edge Research Snapshot

Read-only persistence layer for Shadow Edge Analyzer results.

This module may read completed trade journals and write research
snapshots. It must never modify trading rules, signals, positions,
pending trades, portfolios, or journals.
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.shadow_edge_analyzer import (
    NUMERIC_FACTORS,
    analyze_candidate_cohort_concentration,
    analyze_candidate_overlap,
    analyze_individual_factors,
    assess_combination_readiness,
    build_candidate_quality_gate,
    calculate_baseline_stats,
    collect_shadow_candidates,
    compare_numeric_factor,
    load_completed_trades,
)


DEFAULT_SNAPSHOT_DIRECTORY = Path(
    "research/shadow_edge_snapshots"
)


def _make_json_safe(value):
    """
    Convert analyzer output into portable JSON-safe values.
    """

    if isinstance(value, dict):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            _make_json_safe(item)
            for item in sorted(
                value,
                key=str,
            )
        ]

    if isinstance(value, float):
        if math.isnan(value):
            return None

        if math.isinf(value):
            if value > 0:
                return "INF"

            return "-INF"

    return value


def build_shadow_snapshot(file_path):
    """
    Build one read-only snapshot of the current Shadow Edge research.
    """

    trades = load_completed_trades(
        file_path
    )

    snapshot = {
        "snapshot_version": 1,
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "source_journal": str(
            file_path
        ),
        "baseline": (
            calculate_baseline_stats(
                trades
            )
        ),
        "categorical_factors": (
            analyze_individual_factors(
                trades
            )
        ),
        "numeric_factors": [
            compare_numeric_factor(
                trades,
                factor,
            )
            for factor in NUMERIC_FACTORS
        ],
        "candidates": (
            collect_shadow_candidates(
                trades
            )
        ),
        "candidate_overlap": (
            analyze_candidate_overlap(
                trades
            )
        ),
        "candidate_cohorts": (
            analyze_candidate_cohort_concentration(
                trades
            )
        ),
        "candidate_quality_gate": (
            build_candidate_quality_gate(
                trades
            )
        ),
        "combination_readiness": (
            assess_combination_readiness(
                trades
            )
        ),
    }

    return _make_json_safe(
        snapshot
    )


def save_shadow_snapshot(
    file_path,
    output_directory=DEFAULT_SNAPSHOT_DIRECTORY,
):
    """
    Save one timestamped Shadow Edge research snapshot.
    """

    snapshot = build_shadow_snapshot(
        file_path
    )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d_%H%M%S"
    )

    output_path = (
        output_directory
        / f"{timestamp}_shadow_edge.json"
    )

    output_path.write_text(
        json.dumps(
            snapshot,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def main():
    file_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "paper_trade_journal.csv"
    )

    output_path = save_shadow_snapshot(
        file_path
    )

    print(
        "Shadow Edge research snapshot saved:"
    )

    print(
        output_path
    )


if __name__ == "__main__":
    main()
