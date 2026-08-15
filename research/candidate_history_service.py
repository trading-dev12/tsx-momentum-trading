"""
Northstar Quant
Candidate History Service

Captures strategy-specific Shadow Edge candidate history.

Research only. Failures in this service must never alter or block
trading signals, queues, positions, portfolios, journals, or EOD
completion.
"""

from pathlib import Path

from research.candidate_history import (
    append_candidate_history_record,
)
from research.shadow_edge_snapshot import (
    build_shadow_snapshot,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

STRATEGY_JOURNALS = {
    "Momentum": (
        PROJECT_ROOT
        / "paper_trade_journal.csv"
    ),
    "52-Week Breakout": (
        PROJECT_ROOT
        / "paper_trade_journal_52week.csv"
    ),
    "Mean Reversion": (
        PROJECT_ROOT
        / "paper_trade_journal_mean_reversion.csv"
    ),
}

DEFAULT_HISTORY_DIRECTORY = (
    PROJECT_ROOT
    / "research"
    / "candidate_history"
)


def capture_strategy_candidate_history(
    strategy_name,
    journal_path,
    output_directory=DEFAULT_HISTORY_DIRECTORY,
):
    """
    Capture one strategy's current research state.
    """

    snapshot = build_shadow_snapshot(
        journal_path
    )

    result = append_candidate_history_record(
        snapshot,
        strategy_name,
        output_directory=output_directory,
    )

    return {
        "success": True,
        "strategy": strategy_name,
        "saved": result["saved"],
        "reason": result["reason"],
        "path": str(
            result["path"]
        ),
    }


def capture_all_candidate_history(
    output_directory=DEFAULT_HISTORY_DIRECTORY,
):
    """
    Capture all strategy histories independently.

    One strategy failure does not stop the remaining strategies.
    """

    results = {}

    for strategy_name, journal_path in (
        STRATEGY_JOURNALS.items()
    ):
        try:
            results[strategy_name] = (
                capture_strategy_candidate_history(
                    strategy_name,
                    journal_path,
                    output_directory=(
                        output_directory
                    ),
                )
            )

        except Exception as error:
            results[strategy_name] = {
                "success": False,
                "strategy": strategy_name,
                "saved": False,
                "reason": "ERROR",
                "path": None,
                "message": str(error),
            }

    success = all(
        result["success"]
        for result in results.values()
    )

    return {
        "success": success,
        "strategies": results,
    }
