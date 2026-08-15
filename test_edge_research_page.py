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


def test_edge_research_page_renders_enrichment_integrity():
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
        "enrichment_integrity": {
            "integrity_status": (
                "NO_MONITORED_TRADES_YET"
            ),
            "monitor_start_date": (
                "2026-08-10"
            ),
            "total_trade_count": 14,
            "fully_enriched_trade_count": 9,
            "overall_coverage_percent": (
                64.28571428571429
            ),
            "monitored_trade_count": 0,
            "monitored_fully_enriched_count": 0,
            "monitored_incomplete_count": 0,
        },
    }

    html = render_edge_research_page(
        data
    )

    assert (
        "Enrichment Integrity"
        in html
    )

    assert (
        "9/14"
        in html
    )

    assert (
        "64.3%"
        in html
    )

    assert (
        "2026-08-10"
        in html
    )

    assert (
        "WAITING FOR NEW TRADES"
        in html
    )

    assert (
        "New Monitored Trades"
        in html
    )


def test_edge_research_page_renders_strategy_selector():
    data = {
        "strategy": "Mean Reversion",
        "research_only_notice": "RESEARCH ONLY",
        "validation": {},
        "baseline": {},
        "enrichment": {},
        "combination_readiness": {},
        "best_candidate": None,
        "candidate_count": 0,
        "source_quality": {},
        "enrichment_integrity": {},
    }

    html = render_edge_research_page(
        data
    )

    assert (
        'href="/edge-research"'
        in html
    )

    assert (
        'href="/edge-research/52-week-breakout"'
        in html
    )

    assert (
        'href="/edge-research/mean-reversion"'
        in html
    )

    assert (
        "Momentum"
        in html
    )

    assert (
        "52-Week Breakout"
        in html
    )

    assert (
        "Mean Reversion Strategy"
        in html
    )

    assert (
        "#4169e1"
        in html
    )


def test_edge_research_page_renders_candidate_stability():
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
        "enrichment_integrity": {},
        "candidate_history": {
            "status": "AVAILABLE",
            "observation_count": 2,
        },
        "candidate_stability": [
            {
                "factor": "atr_percent",
                "value": "HIGH",
                "currently_present": True,
                "stability_status": "IMPROVING",
                "observation_count": 2,
                "first_trade_count": 15,
                "latest_trade_count": 20,
                "trade_count_change": 5.0,
                "first_expectancy": 10.0,
                "latest_expectancy": 12.0,
                "expectancy_change": 2.0,
                "first_profit_factor": 1.5,
                "latest_profit_factor": 1.8,
                "profit_factor_change": 0.3,
                "first_win_rate": 55.0,
                "latest_win_rate": 58.0,
                "win_rate_change": 3.0,
            }
        ],
    }

    html = render_edge_research_page(
        data
    )

    assert "Candidate Stability" in html
    assert "AVAILABLE" in html
    assert "History Observations" in html
    assert "ATR Percent: HIGH" in html
    assert "IMPROVING" in html
    assert "Presence: CURRENT" in html
    assert "15" in html
    assert "20" in html
    assert "+5" in html
    assert "$10.00" in html
    assert "$12.00" in html
    assert "+$2.00" in html
    assert "1.50" in html
    assert "1.80" in html
    assert "+0.30" in html
    assert "55.00%" in html
    assert "58.00%" in html
    assert "+3.00 pts" in html


def test_edge_research_page_renders_disappeared_candidate():
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
        "enrichment_integrity": {},
        "candidate_history": {
            "status": "AVAILABLE",
            "observation_count": 3,
        },
        "candidate_stability": [
            {
                "factor": "market_regime",
                "value": "BULL",
                "currently_present": False,
                "stability_status": "DISAPPEARED",
                "observation_count": 2,
                "first_trade_count": 8,
                "latest_trade_count": 11,
                "trade_count_change": 3.0,
                "first_expectancy": 6.0,
                "latest_expectancy": 4.0,
                "expectancy_change": -2.0,
                "first_profit_factor": 1.4,
                "latest_profit_factor": 1.2,
                "profit_factor_change": -0.2,
                "first_win_rate": 60.0,
                "latest_win_rate": 54.0,
                "win_rate_change": -6.0,
            }
        ],
    }

    html = render_edge_research_page(
        data
    )

    assert "Market Regime: BULL" in html
    assert "DISAPPEARED" in html
    assert "Presence: DISAPPEARED" in html


def test_edge_research_page_candidate_stability_no_history():
    data = {
        "strategy": "Mean Reversion",
        "research_only_notice": "RESEARCH ONLY",
        "validation": {},
        "baseline": {},
        "enrichment": {},
        "combination_readiness": {},
        "best_candidate": None,
        "candidate_count": 0,
        "source_quality": {},
        "enrichment_integrity": {},
        "candidate_history": {
            "status": "NO_HISTORY_YET",
            "observation_count": 0,
        },
        "candidate_stability": [],
    }

    html = render_edge_research_page(
        data
    )

    assert "Candidate Stability" in html
    assert "NO HISTORY YET" in html

    assert (
        "first automatic EOD"
        in html
    )


def test_edge_research_page_candidate_stability_unavailable():
    data = {
        "strategy": "52-Week Breakout",
        "research_only_notice": "RESEARCH ONLY",
        "validation": {},
        "baseline": {},
        "enrichment": {},
        "combination_readiness": {},
        "best_candidate": None,
        "candidate_count": 0,
        "source_quality": {},
        "enrichment_integrity": {},
        "candidate_history": {
            "status": "UNAVAILABLE",
            "observation_count": 0,
            "message": "simulated history error",
        },
        "candidate_stability": [],
    }

    html = render_edge_research_page(
        data
    )

    assert "Candidate Stability" in html
    assert "UNAVAILABLE" in html
    assert "simulated history error" in html


def test_edge_research_page_renders_candidate_persistence():
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
        "enrichment_integrity": {},
        "candidate_history": {
            "status": "AVAILABLE",
            "observation_count": 3,
        },
        "candidate_stability": [
            {
                "factor": "atr_percent",
                "value": "HIGH",
                "currently_present": True,
                "stability_status": "REAPPEARED",
                "observation_count": 2,
                "presence_rate_percent": 66.67,
                "current_streak": 1,
                "disappearance_count": 1,
                "reappearance_count": 1,
                "first_trade_count": 5,
                "latest_trade_count": 7,
                "trade_count_change": 2,
                "first_expectancy": 10.0,
                "latest_expectancy": 12.0,
                "expectancy_change": 2.0,
                "first_profit_factor": 1.5,
                "latest_profit_factor": 1.7,
                "profit_factor_change": 0.2,
                "first_win_rate": 60.0,
                "latest_win_rate": 62.0,
                "win_rate_change": 2.0,
            }
        ],
    }

    html = render_edge_research_page(
        data
    )

    assert "REAPPEARED" in html
    assert "Presence Rate" in html
    assert "66.7%" in html
    assert "Current Streak" in html
    assert "Disappearances" in html
    assert "Reappearances" in html
