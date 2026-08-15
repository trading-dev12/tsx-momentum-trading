from research.candidate_history import (
    append_candidate_history_record,
    build_candidate_history_record,
    load_candidate_history,
    normalize_strategy_name,
)


def _snapshot(
    *,
    generated_at="2026-08-14T18:00:00+00:00",
    trade_count=30,
    expectancy=12.5,
    candidates=True,
):
    quality_gate = []

    if candidates:
        quality_gate.append(
            {
                "factor_type": "NUMERIC",
                "factor": "atr_percent",
                "value": "HIGH",
                "minimum_value": 3.0,
                "maximum_value": 6.0,
                "trade_count": trade_count,
                "win_rate": 60.0,
                "profit_factor": 1.8,
                "expectancy": expectancy,
                "baseline_expectancy": 5.0,
                "expectancy_delta": expectancy - 5.0,
                "status": "PROMISING",
                "direction": "BETTER_THAN_BASELINE",
                "cohort_status": "PASS",
                "cohort_concentration_percent": 25.0,
                "research_rating": "PROMISING_REVIEW",
            }
        )

    return {
        "snapshot_version": 1,
        "generated_at_utc": generated_at,
        "source_journal": "paper_trade_journal.csv",
        "baseline": {
            "trade_count": trade_count,
        },
        "candidate_quality_gate": quality_gate,
    }


def test_strategy_name_normalization():
    assert (
        normalize_strategy_name(
            "52-Week Breakout"
        )
        == "52_week_breakout"
    )

    assert (
        normalize_strategy_name(
            "Mean Reversion"
        )
        == "mean_reversion"
    )


def test_build_candidate_history_record_is_compact():
    record = build_candidate_history_record(
        _snapshot(),
        "Momentum",
    )

    assert record["history_version"] == 1
    assert record["strategy"] == "Momentum"
    assert record["strategy_slug"] == "momentum"
    assert record["completed_trade_count"] == 30
    assert record["candidate_count"] == 1

    candidate = record["candidates"][0]

    assert (
        candidate["candidate_id"]
        == "NUMERIC|atr_percent|HIGH"
    )

    assert candidate["trade_count"] == 30
    assert candidate["profit_factor"] == 1.8
    assert candidate["expectancy"] == 12.5
    assert (
        candidate["research_rating"]
        == "PROMISING_REVIEW"
    )


def test_first_record_is_saved(tmp_path):
    result = append_candidate_history_record(
        _snapshot(),
        "Momentum",
        output_directory=tmp_path,
    )

    assert result["saved"] is True
    assert result["reason"] == "CHANGED"

    history = load_candidate_history(
        result["path"]
    )

    assert len(history) == 1
    assert (
        history[0]["completed_trade_count"]
        == 30
    )


def test_identical_research_state_is_not_duplicated(
    tmp_path,
):
    first = append_candidate_history_record(
        _snapshot(
            generated_at=(
                "2026-08-14T18:00:00+00:00"
            )
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    second = append_candidate_history_record(
        _snapshot(
            generated_at=(
                "2026-08-14T19:00:00+00:00"
            )
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    assert first["saved"] is True
    assert second["saved"] is False
    assert second["reason"] == "UNCHANGED"

    history = load_candidate_history(
        first["path"]
    )

    assert len(history) == 1


def test_changed_candidate_state_is_appended(
    tmp_path,
):
    first = append_candidate_history_record(
        _snapshot(
            trade_count=30,
            expectancy=12.5,
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    second = append_candidate_history_record(
        _snapshot(
            generated_at=(
                "2026-08-15T18:00:00+00:00"
            ),
            trade_count=31,
            expectancy=10.0,
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    assert first["saved"] is True
    assert second["saved"] is True

    history = load_candidate_history(
        first["path"]
    )

    assert len(history) == 2
    assert (
        history[0]["completed_trade_count"]
        == 30
    )
    assert (
        history[1]["completed_trade_count"]
        == 31
    )

    assert (
        history[0]["candidates"][0][
            "expectancy"
        ]
        == 12.5
    )

    assert (
        history[1]["candidates"][0][
            "expectancy"
        ]
        == 10.0
    )


def test_candidate_disappearance_is_recorded(
    tmp_path,
):
    first = append_candidate_history_record(
        _snapshot(
            trade_count=30,
            candidates=True,
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    second = append_candidate_history_record(
        _snapshot(
            generated_at=(
                "2026-08-16T18:00:00+00:00"
            ),
            trade_count=35,
            candidates=False,
        ),
        "Momentum",
        output_directory=tmp_path,
    )

    history = load_candidate_history(
        first["path"]
    )

    assert first["saved"] is True
    assert second["saved"] is True
    assert len(history) == 2

    assert history[0]["candidate_count"] == 1
    assert history[1]["candidate_count"] == 0


def test_strategy_histories_are_independent(
    tmp_path,
):
    momentum = append_candidate_history_record(
        _snapshot(),
        "Momentum",
        output_directory=tmp_path,
    )

    mean_reversion = (
        append_candidate_history_record(
            _snapshot(),
            "Mean Reversion",
            output_directory=tmp_path,
        )
    )

    assert (
        momentum["path"].name
        == "momentum.jsonl"
    )

    assert (
        mean_reversion["path"].name
        == "mean_reversion.jsonl"
    )

    assert momentum["path"] != mean_reversion["path"]

    assert len(
        load_candidate_history(
            momentum["path"]
        )
    ) == 1

    assert len(
        load_candidate_history(
            mean_reversion["path"]
        )
    ) == 1

from research.candidate_history import (
    analyze_candidate_history,
    classify_candidate_stability,
)


def _candidate(
    *,
    expectancy=10.0,
    profit_factor=1.5,
    win_rate=55.0,
    trade_count=30,
):
    return {
        "candidate_id": (
            "NUMERIC|atr_percent|HIGH"
        ),
        "factor_type": "NUMERIC",
        "factor": "atr_percent",
        "value": "HIGH",
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "win_rate": win_rate,
        "trade_count": trade_count,
    }


def _history_record(
    timestamp,
    trade_count,
    candidates,
):
    return {
        "generated_at_utc": timestamp,
        "completed_trade_count": (
            trade_count
        ),
        "candidates": candidates,
    }


def test_candidate_stability_new():
    latest = _candidate()

    assert (
        classify_candidate_stability(
            latest,
            None,
        )
        == "NEW"
    )


def test_candidate_stability_improving():
    previous = _candidate(
        expectancy=10.0,
        profit_factor=1.5,
        win_rate=55.0,
    )

    latest = _candidate(
        expectancy=12.0,
        profit_factor=1.8,
        win_rate=58.0,
    )

    assert (
        classify_candidate_stability(
            latest,
            previous,
        )
        == "IMPROVING"
    )


def test_candidate_stability_deteriorating():
    previous = _candidate(
        expectancy=12.0,
        profit_factor=1.8,
        win_rate=60.0,
    )

    latest = _candidate(
        expectancy=8.0,
        profit_factor=1.3,
        win_rate=52.0,
    )

    assert (
        classify_candidate_stability(
            latest,
            previous,
        )
        == "DETERIORATING"
    )


def test_candidate_stability_mixed():
    previous = _candidate(
        expectancy=10.0,
        profit_factor=1.5,
        win_rate=55.0,
    )

    latest = _candidate(
        expectancy=12.0,
        profit_factor=1.3,
        win_rate=55.0,
    )

    assert (
        classify_candidate_stability(
            latest,
            previous,
        )
        == "MIXED"
    )


def test_candidate_stability_stable():
    candidate = _candidate()

    assert (
        classify_candidate_stability(
            candidate,
            dict(candidate),
        )
        == "STABLE"
    )


def test_candidate_history_tracks_growth():
    history = [
        _history_record(
            "2026-08-14T18:00:00+00:00",
            30,
            [
                _candidate(
                    expectancy=10.0,
                    profit_factor=1.5,
                    win_rate=55.0,
                    trade_count=15,
                )
            ],
        ),
        _history_record(
            "2026-08-15T18:00:00+00:00",
            35,
            [
                _candidate(
                    expectancy=12.0,
                    profit_factor=1.8,
                    win_rate=58.0,
                    trade_count=20,
                )
            ],
        ),
    ]

    results = analyze_candidate_history(
        history
    )

    assert len(results) == 1

    candidate = results[0]

    assert (
        candidate["candidate_id"]
        == "NUMERIC|atr_percent|HIGH"
    )

    assert (
        candidate["stability_status"]
        == "IMPROVING"
    )

    assert (
        candidate["currently_present"]
        is True
    )

    assert (
        candidate["observation_count"]
        == 2
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
        candidate["trade_count_change"]
        == 5.0
    )

    assert (
        candidate["expectancy_change"]
        == 2.0
    )


def test_candidate_history_detects_disappearance():
    history = [
        _history_record(
            "2026-08-14T18:00:00+00:00",
            30,
            [
                _candidate(
                    trade_count=15
                )
            ],
        ),
        _history_record(
            "2026-08-15T18:00:00+00:00",
            35,
            [],
        ),
    ]

    results = analyze_candidate_history(
        history
    )

    assert len(results) == 1

    candidate = results[0]

    assert (
        candidate["currently_present"]
        is False
    )

    assert (
        candidate["stability_status"]
        == "DISAPPEARED"
    )

    assert (
        candidate["observation_count"]
        == 1
    )


def test_candidate_history_detects_reappearance():
    history = [
        _history_record(
            "2026-08-14T18:00:00+00:00",
            30,
            [
                _candidate(
                    trade_count=15
                )
            ],
        ),
        _history_record(
            "2026-08-15T18:00:00+00:00",
            32,
            [],
        ),
        _history_record(
            "2026-08-16T18:00:00+00:00",
            35,
            [
                _candidate(
                    trade_count=18
                )
            ],
        ),
    ]

    results = analyze_candidate_history(
        history
    )

    assert len(results) == 1

    candidate = results[0]

    assert (
        candidate["stability_status"]
        == "REAPPEARED"
    )

    assert (
        candidate["currently_present"]
        is True
    )

    assert candidate["presence_count"] == 2
    assert candidate["total_history_records"] == 3

    assert (
        candidate["presence_rate_percent"]
        == 66.67
    )

    assert candidate["current_streak"] == 1

    assert (
        candidate["disappearance_count"]
        == 1
    )

    assert (
        candidate["reappearance_count"]
        == 1
    )


def test_candidate_history_tracks_continuous_presence():
    history = [
        _history_record(
            "2026-08-14T18:00:00+00:00",
            30,
            [_candidate(trade_count=15)],
        ),
        _history_record(
            "2026-08-15T18:00:00+00:00",
            32,
            [_candidate(trade_count=17)],
        ),
        _history_record(
            "2026-08-16T18:00:00+00:00",
            35,
            [_candidate(trade_count=20)],
        ),
    ]

    candidate = (
        analyze_candidate_history(
            history
        )[0]
    )

    assert candidate["presence_count"] == 3

    assert (
        candidate["presence_rate_percent"]
        == 100.0
    )

    assert candidate["current_streak"] == 3

    assert (
        candidate["disappearance_count"]
        == 0
    )

    assert (
        candidate["reappearance_count"]
        == 0
    )
