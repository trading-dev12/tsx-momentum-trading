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

    monkeypatch.setattr(
        edge_research_data,
        "load_candidate_history",
        lambda history_path: [],
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


def _candidate_history_test_snapshot():
    return {
        "snapshot_version": 1,
        "baseline": {
            "trade_count": 35,
            "win_rate": 55.0,
            "profit_factor": 1.4,
            "expectancy": 5.0,
        },
        "candidate_quality_gate": [],
        "combination_readiness": {
            "status": "NOT_READY",
            "fully_enriched_trade_count": 20,
            "minimum_enriched_trades": 60,
            "distinct_entry_date_count": 7,
            "minimum_distinct_entry_dates": 10,
            "validation_trade_target": 200,
        },
    }


def _prepare_candidate_history_dashboard_test(
    monkeypatch,
):
    monkeypatch.setattr(
        edge_research_data,
        "build_shadow_snapshot",
        lambda journal_path: (
            _candidate_history_test_snapshot()
        ),
    )

    monkeypatch.setattr(
        edge_research_data,
        "calculate_research_source_coverage",
        lambda journal_path: {},
    )


def test_edge_research_candidate_history_no_history_yet(
    monkeypatch,
    tmp_path,
):
    _prepare_candidate_history_dashboard_test(
        monkeypatch
    )

    monkeypatch.setattr(
        edge_research_data,
        "load_candidate_history",
        lambda history_path: [],
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "paper_trade_journal.csv",
            strategy_name="Momentum",
            history_directory=tmp_path,
        )
    )

    assert (
        result["candidate_history"]["status"]
        == "NO_HISTORY_YET"
    )

    assert (
        result["candidate_history"][
            "observation_count"
        ]
        == 0
    )

    assert (
        result["candidate_stability"]
        == []
    )

    assert (
        result["current_candidate_stability"]
        == []
    )


def test_edge_research_candidate_history_available(
    monkeypatch,
    tmp_path,
):
    _prepare_candidate_history_dashboard_test(
        monkeypatch
    )

    history = [
        {
            "generated_at_utc": (
                "2026-08-14T18:00:00+00:00"
            ),
            "completed_trade_count": 30,
            "candidates": [
                {
                    "candidate_id": (
                        "NUMERIC|atr_percent|HIGH"
                    ),
                    "factor_type": "NUMERIC",
                    "factor": "atr_percent",
                    "value": "HIGH",
                    "trade_count": 15,
                    "expectancy": 10.0,
                    "profit_factor": 1.5,
                    "win_rate": 55.0,
                }
            ],
        },
        {
            "generated_at_utc": (
                "2026-08-15T18:00:00+00:00"
            ),
            "completed_trade_count": 35,
            "candidates": [
                {
                    "candidate_id": (
                        "NUMERIC|atr_percent|HIGH"
                    ),
                    "factor_type": "NUMERIC",
                    "factor": "atr_percent",
                    "value": "HIGH",
                    "trade_count": 20,
                    "expectancy": 12.0,
                    "profit_factor": 1.8,
                    "win_rate": 58.0,
                }
            ],
        },
    ]

    monkeypatch.setattr(
        edge_research_data,
        "load_candidate_history",
        lambda history_path: history,
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "paper_trade_journal.csv",
            strategy_name="Momentum",
            history_directory=tmp_path,
        )
    )

    assert (
        result["candidate_history"]["status"]
        == "AVAILABLE"
    )

    assert (
        result["candidate_history"][
            "observation_count"
        ]
        == 2
    )

    assert (
        result["candidate_stability_count"]
        == 1
    )

    candidate = (
        result[
            "current_candidate_stability"
        ][0]
    )

    assert (
        candidate["stability_status"]
        == "IMPROVING"
    )

    assert (
        candidate["first_trade_count"]
        == 15
    )

    assert (
        candidate["latest_trade_count"]
        == 20
    )

    assert (
        candidate["expectancy_change"]
        == 2.0
    )


def test_edge_research_candidate_history_strategy_path(
    monkeypatch,
    tmp_path,
):
    _prepare_candidate_history_dashboard_test(
        monkeypatch
    )

    captured_paths = []

    def fake_load_candidate_history(
        history_path,
    ):
        captured_paths.append(
            history_path
        )
        return []

    monkeypatch.setattr(
        edge_research_data,
        "load_candidate_history",
        fake_load_candidate_history,
    )

    strategies = [
        (
            "Momentum",
            "momentum.jsonl",
        ),
        (
            "52-Week Breakout",
            "52_week_breakout.jsonl",
        ),
        (
            "Mean Reversion",
            "mean_reversion.jsonl",
        ),
    ]

    for strategy_name, expected_name in strategies:
        (
            edge_research_data
            .build_edge_research_dashboard_data(
                "journal.csv",
                strategy_name=strategy_name,
                history_directory=tmp_path,
            )
        )

        assert (
            captured_paths[-1].name
            == expected_name
        )


def test_edge_research_candidate_history_unavailable(
    monkeypatch,
    tmp_path,
):
    _prepare_candidate_history_dashboard_test(
        monkeypatch
    )

    def failing_history_loader(
        history_path,
    ):
        raise ValueError(
            "simulated corrupt history"
        )

    monkeypatch.setattr(
        edge_research_data,
        "load_candidate_history",
        failing_history_loader,
    )

    result = (
        edge_research_data
        .build_edge_research_dashboard_data(
            "paper_trade_journal.csv",
            strategy_name="Momentum",
            history_directory=tmp_path,
        )
    )

    assert (
        result["candidate_history"]["status"]
        == "UNAVAILABLE"
    )

    assert (
        "simulated corrupt history"
        in result[
            "candidate_history"
        ]["message"]
    )

    assert (
        result["candidate_stability"]
        == []
    )
