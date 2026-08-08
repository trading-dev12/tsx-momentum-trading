"""
Northstar Quant
Edge Research Dashboard Data

Read-only adapter between Shadow Edge research results
and the mobile dashboard.

This module never changes trading rules, signals,
positions, portfolios, pending trades, or journals.
"""

from research.research_data_quality import (
    calculate_research_source_coverage,
)
from research.shadow_edge_snapshot import (
    build_shadow_snapshot,
)


VALIDATION_TRADE_TARGET = 200

RESEARCH_ONLY_NOTICE = (
    "RESEARCH ONLY - Strategy rules remain frozen "
    "until the 200-trade validation review."
)


def _progress_percent(
    current,
    target,
):
    """
    Return a capped progress percentage.
    """

    if not target:
        return 0.0

    return round(
        min(
            100.0,
            (
                float(current)
                / float(target)
            )
            * 100.0,
        ),
        2,
    )


def build_edge_research_dashboard_data(
    journal_path,
    strategy_name="Momentum",
):
    """
    Build one read-only Edge Research dashboard summary.
    """

    snapshot = build_shadow_snapshot(
        journal_path
    )

    source_quality = (
        calculate_research_source_coverage(
            journal_path
        )
    )

    baseline = snapshot.get(
        "baseline",
        {},
    )

    readiness = snapshot.get(
        "combination_readiness",
        {},
    )

    quality_gate = snapshot.get(
        "candidate_quality_gate",
        [],
    )

    completed_trades = int(
        baseline.get(
            "trade_count",
            0,
        )
        or 0
    )

    validation_target = int(
        readiness.get(
            "validation_trade_target",
            VALIDATION_TRADE_TARGET,
        )
        or VALIDATION_TRADE_TARGET
    )

    enriched_trades = int(
        readiness.get(
            "fully_enriched_trade_count",
            0,
        )
        or 0
    )

    enriched_target = int(
        readiness.get(
            "minimum_enriched_trades",
            60,
        )
        or 60
    )

    distinct_dates = int(
        readiness.get(
            "distinct_entry_date_count",
            0,
        )
        or 0
    )

    distinct_date_target = int(
        readiness.get(
            "minimum_distinct_entry_dates",
            10,
        )
        or 10
    )

    best_candidate = (
        quality_gate[0]
        if quality_gate
        else None
    )

    return {
        "strategy": strategy_name,
        "research_only_notice": (
            RESEARCH_ONLY_NOTICE
        ),
        "validation": {
            "completed_trades": (
                completed_trades
            ),
            "target": validation_target,
            "progress_percent": (
                _progress_percent(
                    completed_trades,
                    validation_target,
                )
            ),
        },
        "baseline": baseline,
        "enrichment": {
            "fully_enriched_trades": (
                enriched_trades
            ),
            "target": enriched_target,
            "progress_percent": (
                _progress_percent(
                    enriched_trades,
                    enriched_target,
                )
            ),
            "distinct_entry_dates": (
                distinct_dates
            ),
            "distinct_entry_date_target": (
                distinct_date_target
            ),
            "date_progress_percent": (
                _progress_percent(
                    distinct_dates,
                    distinct_date_target,
                )
            ),
        },
        "combination_readiness": (
            readiness
        ),
        "best_candidate": (
            best_candidate
        ),
        "candidate_count": len(
            quality_gate
        ),
        "source_quality": (
            source_quality
        ),
        "snapshot_version": snapshot.get(
            "snapshot_version",
            1,
        ),
    }
