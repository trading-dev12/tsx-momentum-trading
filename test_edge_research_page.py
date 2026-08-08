from mobile_dashboard.edge_research_page import (
    render_edge_research_page,
)


def test_edge_research_page_renders():
    data = {
        "strategy": "Momentum",
        "research_only_notice": (
            "RESEARCH ONLY - Strategy rules remain frozen "
            "until the 200-trade validation review."
        ),
        "validation": {
            "completed_trades": 14,
            "target": 200,
            "progress_percent": 7.0,
        },
        "baseline": {
            "win_rate": 57.14,
            "profit_factor": 0.8678,
            "expectancy": -4.31,
            "sample_status": "VERY_EARLY",
        },
        "enrichment": {
            "fully_enriched_trades": 9,
            "target": 60,
            "progress_percent": 15.0,
            "distinct_entry_dates": 5,
            "distinct_entry_date_target": 10,
            "date_progress_percent": 50.0,
        },
        "combination_readiness": {
            "status": "NOT_READY",
        },
        "best_candidate": {
            "factor": "volatility_regime",
            "value": "NORMAL",
            "research_rating": "WATCH_ONLY",
            "trade_count": 7,
            "win_rate": 71.43,
            "profit_factor": 1.2678,
            "expectancy": 7.56,
        },
        "candidate_count": 13,
        "source_quality": {
            "recorded_coverage_percent": 0.0,
            "ibkr_percent_of_recorded": 0.0,
            "fallback_source_observations": 0,
            "status": (
                "SOURCE_TRACKING_NOT_YET_RECORDED"
            ),
        },
    }

    html = render_edge_research_page(
        data
    )

    assert "Edge Research" in html
    assert "Momentum Strategy" in html
    assert "14/200" in html
    assert "57.14%" in html
    assert "0.87" in html
    assert "-$4.31" in html
    assert "9/60" in html
    assert "5/10" in html
    assert "NOT READY" in html
    assert "Volatility Regime: NORMAL" in html
    assert "WATCH ONLY" in html
    assert "Quality-gated candidates:" in html
    assert "13" in html


def test_edge_research_page_handles_no_candidate():
    data = {
        "strategy": "Momentum",
        "research_only_notice": "RESEARCH ONLY",
        "validation": {},
        "baseline": {},
        "enrichment": {},
        "combination_readiness": {},
        "best_candidate": None,
        "candidate_count": 0,
        "source_quality": {},
    }

    html = render_edge_research_page(
        data
    )

    assert (
        "No current research candidate."
        in html
    )

    assert (
        "No strategy or trading controls"
        in html
    )
