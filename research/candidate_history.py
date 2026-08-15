"""
Northstar Quant
Candidate History and Stability Tracking

Append-only research history for Shadow Edge candidates.

This module may read Shadow Edge research snapshots and write
research-history records. It must never modify trading rules,
signals, positions, pending trades, portfolios, or journals.
"""

import json
from pathlib import Path


DEFAULT_HISTORY_DIRECTORY = Path(
    "research/candidate_history"
)


def normalize_strategy_name(strategy_name):
    """
    Convert a display strategy name into a stable file slug.
    """

    return (
        str(strategy_name)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def candidate_identity(candidate):
    """
    Build a stable identity for one research candidate.
    """

    return "|".join(
        [
            str(
                candidate.get(
                    "factor_type",
                    "",
                )
            ),
            str(
                candidate.get(
                    "factor",
                    "",
                )
            ),
            str(
                candidate.get(
                    "value",
                    "",
                )
            ),
        ]
    )


def build_candidate_history_record(
    snapshot,
    strategy_name,
):
    """
    Build a compact history record from one Shadow Edge snapshot.
    """

    baseline = snapshot.get(
        "baseline",
        {},
    )

    candidates = []

    for candidate in snapshot.get(
        "candidate_quality_gate",
        [],
    ):
        candidates.append(
            {
                "candidate_id": (
                    candidate_identity(
                        candidate
                    )
                ),
                "factor_type": candidate.get(
                    "factor_type"
                ),
                "factor": candidate.get(
                    "factor"
                ),
                "value": candidate.get(
                    "value"
                ),
                "minimum_value": candidate.get(
                    "minimum_value"
                ),
                "maximum_value": candidate.get(
                    "maximum_value"
                ),
                "trade_count": candidate.get(
                    "trade_count",
                    0,
                ),
                "win_rate": candidate.get(
                    "win_rate",
                    0.0,
                ),
                "profit_factor": candidate.get(
                    "profit_factor"
                ),
                "expectancy": candidate.get(
                    "expectancy",
                    0.0,
                ),
                "baseline_expectancy": (
                    candidate.get(
                        "baseline_expectancy",
                        0.0,
                    )
                ),
                "expectancy_delta": (
                    candidate.get(
                        "expectancy_delta",
                        0.0,
                    )
                ),
                "status": candidate.get(
                    "status"
                ),
                "direction": candidate.get(
                    "direction"
                ),
                "cohort_status": candidate.get(
                    "cohort_status"
                ),
                "cohort_concentration_percent": (
                    candidate.get(
                        "cohort_concentration_percent",
                        0.0,
                    )
                ),
                "research_rating": candidate.get(
                    "research_rating"
                ),
            }
        )

    return {
        "history_version": 1,
        "generated_at_utc": snapshot.get(
            "generated_at_utc"
        ),
        "strategy": strategy_name,
        "strategy_slug": (
            normalize_strategy_name(
                strategy_name
            )
        ),
        "source_journal": snapshot.get(
            "source_journal"
        ),
        "completed_trade_count": baseline.get(
            "trade_count",
            0,
        ),
        "candidate_count": len(
            candidates
        ),
        "candidates": candidates,
    }


def _record_payload(record):
    """
    Return the data used to determine whether history changed.

    Timestamp is intentionally excluded.
    """

    return {
        key: value
        for key, value in record.items()
        if key != "generated_at_utc"
    }


def load_candidate_history(history_file):
    """
    Load an append-only candidate history JSONL file.
    """

    history_file = Path(
        history_file
    )

    if not history_file.exists():
        return []

    records = []

    with history_file.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            records.append(
                json.loads(
                    line
                )
            )

    return records


def append_candidate_history_record(
    snapshot,
    strategy_name,
    output_directory=DEFAULT_HISTORY_DIRECTORY,
):
    """
    Append one candidate-history record if research state changed.

    Repeated dashboard/EOD runs with identical research data do not
    create duplicate history records.
    """

    record = (
        build_candidate_history_record(
            snapshot,
            strategy_name,
        )
    )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    history_file = (
        output_directory
        / (
            record["strategy_slug"]
            + ".jsonl"
        )
    )

    existing = load_candidate_history(
        history_file
    )

    if existing:
        if (
            _record_payload(
                existing[-1]
            )
            == _record_payload(
                record
            )
        ):
            return {
                "saved": False,
                "reason": "UNCHANGED",
                "path": history_file,
                "record": record,
            }

    with history_file.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                record,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )

    return {
        "saved": True,
        "reason": "CHANGED",
        "path": history_file,
        "record": record,
    }


def _numeric_delta(current, previous):
    """
    Safely calculate the change between two numeric values.
    """

    if current is None or previous is None:
        return None

    try:
        return float(current) - float(previous)
    except (TypeError, ValueError):
        return None


def _direction_from_delta(
    value,
    tolerance=0.000001,
):
    """
    Convert a numeric change into a descriptive direction.
    """

    if value is None:
        return "UNKNOWN"

    if value > tolerance:
        return "UP"

    if value < -tolerance:
        return "DOWN"

    return "FLAT"


def classify_candidate_stability(
    latest,
    previous,
):
    """
    Classify how one candidate changed between observations.

    This is descriptive research only.
    """

    if latest is None:
        return "DISAPPEARED"

    if previous is None:
        return "NEW"

    expectancy_delta = _numeric_delta(
        latest.get("expectancy"),
        previous.get("expectancy"),
    )

    profit_factor_delta = _numeric_delta(
        latest.get("profit_factor"),
        previous.get("profit_factor"),
    )

    win_rate_delta = _numeric_delta(
        latest.get("win_rate"),
        previous.get("win_rate"),
    )

    directions = [
        _direction_from_delta(
            expectancy_delta
        ),
        _direction_from_delta(
            profit_factor_delta
        ),
        _direction_from_delta(
            win_rate_delta
        ),
    ]

    known = [
        direction
        for direction in directions
        if direction != "UNKNOWN"
    ]

    if not known:
        return "UNKNOWN"

    if all(
        direction == "FLAT"
        for direction in known
    ):
        return "STABLE"

    positive = sum(
        direction == "UP"
        for direction in known
    )

    negative = sum(
        direction == "DOWN"
        for direction in known
    )

    if positive >= 2 and negative == 0:
        return "IMPROVING"

    if negative >= 2 and positive == 0:
        return "DETERIORATING"

    return "MIXED"


def analyze_candidate_history(
    history_records,
):
    """
    Analyze candidate persistence and metric changes over time.

    Candidates are followed by stable candidate_id.
    """

    if not history_records:
        return []

    observations = {}

    for record_index, record in enumerate(
        history_records
    ):
        for candidate in record.get(
            "candidates",
            [],
        ):
            candidate_id = candidate.get(
                "candidate_id"
            )

            if not candidate_id:
                continue

            observations.setdefault(
                candidate_id,
                [],
            ).append(
                {
                    "record_index": record_index,
                    "generated_at_utc": (
                        record.get(
                            "generated_at_utc"
                        )
                    ),
                    "completed_trade_count": (
                        record.get(
                            "completed_trade_count",
                            0,
                        )
                    ),
                    "candidate": candidate,
                }
            )

    latest_record_index = (
        len(history_records) - 1
    )

    results = []

    for candidate_id, candidate_history in (
        observations.items()
    ):
        first_observation = (
            candidate_history[0]
        )

        last_observation = (
            candidate_history[-1]
        )

        currently_present = (
            last_observation[
                "record_index"
            ]
            == latest_record_index
        )

        present_record_indices = {
            observation["record_index"]
            for observation in candidate_history
        }

        presence_count = len(
            present_record_indices
        )

        presence_rate_percent = round(
            (
                presence_count
                / len(history_records)
            )
            * 100.0,
            2,
        )

        first_seen_index = (
            first_observation[
                "record_index"
            ]
        )

        previous_record_present = (
            latest_record_index > 0
            and (
                latest_record_index - 1
                in present_record_indices
            )
        )

        current_streak = 0

        if currently_present:
            for record_index in range(
                latest_record_index,
                -1,
                -1,
            ):
                if (
                    record_index
                    not in present_record_indices
                ):
                    break

                current_streak += 1

        disappearance_count = 0
        reappearance_count = 0
        was_present = False
        seen_once = False

        for record_index in range(
            first_seen_index,
            latest_record_index + 1,
        ):
            is_present = (
                record_index
                in present_record_indices
            )

            if is_present:
                if (
                    seen_once
                    and not was_present
                ):
                    reappearance_count += 1

                seen_once = True

            elif was_present:
                disappearance_count += 1

            was_present = is_present

        latest_candidate = (
            last_observation["candidate"]
            if currently_present
            else None
        )

        previous_candidate = None
        reappeared = False

        if currently_present:
            if (
                first_seen_index
                == latest_record_index
            ):
                previous_candidate = None

            elif not previous_record_present:
                reappeared = True

                if len(candidate_history) >= 2:
                    previous_candidate = (
                        candidate_history[-2][
                            "candidate"
                        ]
                    )

            elif len(candidate_history) >= 2:
                previous_candidate = (
                    candidate_history[-2][
                        "candidate"
                    ]
                )

        else:
            previous_candidate = (
                last_observation[
                    "candidate"
                ]
            )

        if reappeared:
            stability_status = (
                "REAPPEARED"
            )
        else:
            stability_status = (
                classify_candidate_stability(
                    latest_candidate,
                    previous_candidate,
                )
            )

        first_candidate = (
            first_observation[
                "candidate"
            ]
        )

        comparison_candidate = (
            latest_candidate
            if latest_candidate is not None
            else previous_candidate
        )

        results.append(
            {
                "candidate_id": candidate_id,
                "factor_type": (
                    first_candidate.get(
                        "factor_type"
                    )
                ),
                "factor": (
                    first_candidate.get(
                        "factor"
                    )
                ),
                "value": (
                    first_candidate.get(
                        "value"
                    )
                ),
                "currently_present": (
                    currently_present
                ),
                "stability_status": (
                    stability_status
                ),
                "observation_count": len(
                    candidate_history
                ),
                "total_history_records": (
                    len(history_records)
                ),
                "presence_count": (
                    presence_count
                ),
                "presence_rate_percent": (
                    presence_rate_percent
                ),
                "current_streak": (
                    current_streak
                ),
                "disappearance_count": (
                    disappearance_count
                ),
                "reappearance_count": (
                    reappearance_count
                ),
                "first_seen_utc": (
                    first_observation[
                        "generated_at_utc"
                    ]
                ),
                "last_seen_utc": (
                    last_observation[
                        "generated_at_utc"
                    ]
                ),
                "first_trade_count": (
                    first_candidate.get(
                        "trade_count",
                        0,
                    )
                ),
                "latest_trade_count": (
                    comparison_candidate.get(
                        "trade_count",
                        0,
                    )
                ),
                "trade_count_change": (
                    _numeric_delta(
                        comparison_candidate.get(
                            "trade_count"
                        ),
                        first_candidate.get(
                            "trade_count"
                        ),
                    )
                ),
                "first_expectancy": (
                    first_candidate.get(
                        "expectancy"
                    )
                ),
                "latest_expectancy": (
                    comparison_candidate.get(
                        "expectancy"
                    )
                ),
                "expectancy_change": (
                    _numeric_delta(
                        comparison_candidate.get(
                            "expectancy"
                        ),
                        first_candidate.get(
                            "expectancy"
                        ),
                    )
                ),
                "first_profit_factor": (
                    first_candidate.get(
                        "profit_factor"
                    )
                ),
                "latest_profit_factor": (
                    comparison_candidate.get(
                        "profit_factor"
                    )
                ),
                "profit_factor_change": (
                    _numeric_delta(
                        comparison_candidate.get(
                            "profit_factor"
                        ),
                        first_candidate.get(
                            "profit_factor"
                        ),
                    )
                ),
                "first_win_rate": (
                    first_candidate.get(
                        "win_rate"
                    )
                ),
                "latest_win_rate": (
                    comparison_candidate.get(
                        "win_rate"
                    )
                ),
                "win_rate_change": (
                    _numeric_delta(
                        comparison_candidate.get(
                            "win_rate"
                        ),
                        first_candidate.get(
                            "win_rate"
                        ),
                    )
                ),
            }
        )

    status_priority = {
        "IMPROVING": 6,
        "STABLE": 5,
        "MIXED": 4,
        "REAPPEARED": 3,
        "NEW": 2,
        "DETERIORATING": 1,
        "DISAPPEARED": 0,
        "UNKNOWN": -1,
    }

    results.sort(
        key=lambda result: (
            status_priority.get(
                result[
                    "stability_status"
                ],
                -1,
            ),
            result[
                "latest_trade_count"
            ],
        ),
        reverse=True,
    )

    return results
