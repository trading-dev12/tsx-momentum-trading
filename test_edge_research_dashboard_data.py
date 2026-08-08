from mobile_dashboard import (
    edge_research_data,
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
