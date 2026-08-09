import pytest

from mobile_dashboard import (
    edge_research_data,
)


@pytest.fixture(autouse=True)
def mock_enrichment_integrity(monkeypatch):
    """
    Keep dashboard-data tests independent of live journals.
    """

    fake_integrity = {
        "integrity_status": (
            "NO_MONITORED_TRADES_YET"
        ),
        "monitor_start_date": (
            "2026-08-10"
        ),
        "total_trade_count": 14,
        "fully_enriched_trade_count": 9,
        "not_fully_enriched_trade_count": 5,
        "overall_coverage_percent": (
            64.28571428571429
        ),
        "legacy_trade_count": 14,
        "undated_trade_count": 0,
        "monitored_trade_count": 0,
        "monitored_fully_enriched_count": 0,
        "monitored_incomplete_count": 0,
        "monitored_coverage_percent": 0.0,
        "missing_factor_counts": {},
        "incomplete_monitored_trades": [],
    }

    monkeypatch.setattr(
        edge_research_data,
        "analyze_enrichment_integrity_journal",
        lambda journal_path: fake_integrity,
    )


def test_edge_research_dashboard_data(
    monkeypatch,
):
    fake_snapshot = {
        "snapshot_version": 1,
        "baseline": {
            "trade_count": 14,
            "win_rate": 57.14,
            "profit_factor": 0.87,
            "expectancy": -4.31,
            "sample_status": "VERY_EARLY",
        },
        "candidate_quality_gate": [
            {
                "factor": (
                    "volatility_regime"
                ),
                "value": "NORMAL",
                "research_rating": (
                    "WATCH_ONLY"
                ),
                "trade_count": 7,
            }
        ],
        "combination_readiness": {
            "status": "NOT_READY",
            "fully_enriched_trade_count": 9,
            "minimum_enriched_trades": 60,
            "distinct_entry_date_count": 5,
            "minimum_distinct_entry_dates": 10,
            "validation_trade_target": 200,
        },
    }

    fake_quality = {
        "trade_count": 14,
        "recorded_coverage_percent": 0.0,
        "ibkr_percent_of_recorded": 0.0,
        "status": (
            "SOURCE_TRACKING_NOT_YET_RECORDED"
        ),
    }

    monkeypatch.setattr(
        edge_research_data,
        "build_shadow_snapshot",
        lambda journal_path: fake_snapshot,
    )

    monkeypatch.setattr(
        edge_research_data,
        "calculate_research_source_coverage",
        lambda journal_path: fake_quality,
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "paper_trade_journal.csv"
        )
    )

    assert result[
        "strategy"
    ] == "Momentum"

    assert result[
        "validation"
    ][
        "completed_trades"
    ] == 14

    assert result[
        "validation"
    ][
        "progress_percent"
    ] == 7.0

    assert result[
        "enrichment"
    ][
        "fully_enriched_trades"
    ] == 9

    assert result[
        "enrichment"
    ][
        "progress_percent"
    ] == 15.0

    assert result[
        "enrichment"
    ][
        "date_progress_percent"
    ] == 50.0

    assert result[
        "best_candidate"
    ][
        "research_rating"
    ] == "WATCH_ONLY"

    assert result[
        "candidate_count"
    ] == 1

    assert result[
        "source_quality"
    ][
        "status"
    ] == (
        "SOURCE_TRACKING_NOT_YET_RECORDED"
    )


def test_edge_research_dashboard_no_candidates(
    monkeypatch,
):
    fake_snapshot = {
        "snapshot_version": 1,
        "baseline": {
            "trade_count": 0,
        },
        "candidate_quality_gate": [],
        "combination_readiness": {
            "status": "NOT_READY",
            "fully_enriched_trade_count": 0,
            "minimum_enriched_trades": 60,
            "distinct_entry_date_count": 0,
            "minimum_distinct_entry_dates": 10,
            "validation_trade_target": 200,
        },
    }

    monkeypatch.setattr(
        edge_research_data,
        "build_shadow_snapshot",
        lambda journal_path: fake_snapshot,
    )

    monkeypatch.setattr(
        edge_research_data,
        "calculate_research_source_coverage",
        lambda journal_path: {},
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "journal.csv"
        )
    )

    assert result[
        "best_candidate"
    ] is None

    assert result[
        "candidate_count"
    ] == 0

    assert result[
        "validation"
    ][
        "progress_percent"
    ] == 0.0

def test_edge_research_dashboard_includes_enrichment_integrity(
    monkeypatch,
):
    fake_snapshot = {
        "snapshot_version": 1,
        "baseline": {
            "trade_count": 14,
        },
        "candidate_quality_gate": [],
        "combination_readiness": {
            "status": "NOT_READY",
            "fully_enriched_trade_count": 9,
            "minimum_enriched_trades": 60,
            "distinct_entry_date_count": 5,
            "minimum_distinct_entry_dates": 10,
            "validation_trade_target": 200,
        },
    }

    monkeypatch.setattr(
        edge_research_data,
        "build_shadow_snapshot",
        lambda journal_path: fake_snapshot,
    )

    monkeypatch.setattr(
        edge_research_data,
        "calculate_research_source_coverage",
        lambda journal_path: {},
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "paper_trade_journal.csv"
        )
    )

    integrity = result[
        "enrichment_integrity"
    ]

    assert (
        integrity["fully_enriched_trade_count"]
        == 9
    )

    assert (
        integrity["total_trade_count"]
        == 14
    )

    assert (
        integrity["monitor_start_date"]
        == "2026-08-10"
    )

    assert (
        integrity["monitored_trade_count"]
        == 0
    )

    assert (
        integrity["integrity_status"]
        == "NO_MONITORED_TRADES_YET"
    )
