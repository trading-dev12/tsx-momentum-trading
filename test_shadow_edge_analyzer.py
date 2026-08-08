import csv

from research.shadow_edge_analyzer import (
    analyze_journal,
    calculate_baseline_stats,
    compare_categorical_factor,
)


def test_calculate_baseline_stats():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "2.0",
        },
        {
            "profit_loss": "-50",
            "profit_loss_percent": "-1.0",
        },
        {
            "profit_loss": "25",
            "profit_loss_percent": "0.5",
        },
        {
            "profit_loss": "-25",
            "profit_loss_percent": "-0.5",
        },
    ]

    result = calculate_baseline_stats(
        trades
    )

    assert result["trade_count"] == 4
    assert result["wins"] == 2
    assert result["losses"] == 2
    assert result["breakeven"] == 0
    assert result["win_rate"] == 50.0
    assert result["gross_profit"] == 125.0
    assert result["gross_loss"] == 75.0

    assert round(
        result["profit_factor"],
        4,
    ) == 1.6667

    assert result["total_profit_loss"] == 50.0
    assert result["expectancy"] == 12.5
    assert result["average_gain"] == 62.5
    assert result["average_loss"] == 37.5
    assert result["average_return_percent"] == 0.25
    assert result["sample_status"] == "VERY_EARLY"


def test_analyze_journal_reads_csv(tmp_path):
    journal = (
        tmp_path / "journal.csv"
    )

    with journal.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "symbol",
                "profit_loss",
                "profit_loss_percent",
            ],
        )

        writer.writeheader()

        writer.writerow(
            {
                "symbol": "ABC.TO",
                "profit_loss": "100",
                "profit_loss_percent": "1.5",
            }
        )

        writer.writerow(
            {
                "symbol": "XYZ.TO",
                "profit_loss": "-50",
                "profit_loss_percent": "-0.75",
            }
        )

    result = analyze_journal(
        journal
    )

    assert result["trade_count"] == 2
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["profit_factor"] == 2.0
    assert result["expectancy"] == 25.0


def test_factor_analysis_excludes_missing_data():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-50",
            "profit_loss_percent": "-1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "20",
            "profit_loss_percent": "0.2",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "-40",
            "profit_loss_percent": "-0.4",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "1000",
            "profit_loss_percent": "10",
            "market_regime": "",
        },
    ]

    result = compare_categorical_factor(
        trades,
        "market_regime",
    )

    assert result["total_trade_count"] == 5
    assert result["eligible_trade_count"] == 4
    assert result["missing_trade_count"] == 1

    assert result[
        "eligible_baseline"
    ]["trade_count"] == 4


def test_small_factor_groups_cannot_be_promising():
    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-25",
            "profit_loss_percent": "-0.25",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "10",
            "profit_loss_percent": "0.1",
            "market_regime": "BEAR",
        },
    ]

    result = compare_categorical_factor(
        trades,
        "market_regime",
        minimum_sample_size=30,
    )

    statuses = {
        group["status"]
        for group in result["groups"]
    }

    assert statuses == {
        "INSUFFICIENT_DATA"
    }


def test_numeric_factor_creates_rank_buckets():
    from research.shadow_edge_analyzer import (
        compare_numeric_factor,
    )

    trades = []

    for value in range(1, 10):
        trades.append(
            {
                "profit_loss": str(
                    value * 10
                ),
                "profit_loss_percent": "1",
                "rs_xic_20": str(value),
            }
        )

    result = compare_numeric_factor(
        trades,
        "rs_xic_20",
    )

    assert result[
        "eligible_trade_count"
    ] == 9

    assert result[
        "missing_trade_count"
    ] == 0

    assert len(
        result["groups"]
    ) == 3

    assert [
        group["value"]
        for group in result["groups"]
    ] == [
        "LOW",
        "MIDDLE",
        "HIGH",
    ]

    assert [
        group["stats"]["trade_count"]
        for group in result["groups"]
    ] == [
        3,
        3,
        3,
    ]


def test_numeric_factor_excludes_missing_values():
    from research.shadow_edge_analyzer import (
        compare_numeric_factor,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "atr_percent": "2.0",
        },
        {
            "profit_loss": "-50",
            "profit_loss_percent": "-1",
            "atr_percent": "3.0",
        },
        {
            "profit_loss": "500",
            "profit_loss_percent": "5",
            "atr_percent": "",
        },
    ]

    result = compare_numeric_factor(
        trades,
        "atr_percent",
    )

    assert result[
        "eligible_trade_count"
    ] == 2

    assert result[
        "missing_trade_count"
    ] == 1

    assert result[
        "eligible_baseline"
    ]["trade_count"] == 2


def test_shadow_report_includes_numeric_section(
    tmp_path,
    capsys,
):
    from research.shadow_edge_analyzer import (
        print_shadow_report,
    )

    journal = (
        tmp_path / "journal.csv"
    )

    fieldnames = [
        "profit_loss",
        "profit_loss_percent",
        "market_regime",
        "ma_trend_alignment",
        "gap_bucket",
        "volatility_regime",
        "rs_xic_20",
        "rs_xiu_20",
        "ma_close_vs_sma20_percent",
        "ma_close_vs_sma50_percent",
        "ma_close_vs_sma200_percent",
        "sector_strength_20",
        "gap_percent",
        "atr_percent",
    ]

    with journal.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerow(
            {
                field: "1"
                for field in fieldnames
            }
        )

    print_shadow_report(
        journal
    )

    output = capsys.readouterr().out

    assert (
        "NUMERIC FACTOR: rs_xic_20"
        in output
    )

    assert (
        "NUMERIC FACTOR: atr_percent"
        in output
    )

    assert (
        "Research only. No trading rules "
        "were modified."
        in output
    )


def test_candidate_tracker_only_keeps_better_groups():
    from research.shadow_edge_analyzer import (
        collect_shadow_candidates,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "80",
            "profit_loss_percent": "0.8",
            "market_regime": "BULL",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
        },
        {
            "profit_loss": "-80",
            "profit_loss_percent": "-0.8",
            "market_regime": "BEAR",
        },
    ]

    candidates = collect_shadow_candidates(
        trades,
        minimum_sample_size=30,
    )

    market_candidates = [
        candidate
        for candidate in candidates
        if candidate["factor"]
        == "market_regime"
    ]

    assert len(
        market_candidates
    ) == 1

    assert market_candidates[
        0
    ]["value"] == "BULL"

    assert market_candidates[
        0
    ]["status"] == "INSUFFICIENT_DATA"


def test_candidate_tracker_prioritizes_sample_size():
    from research.shadow_edge_analyzer import (
        collect_shadow_candidates,
    )

    trades = []

    for index in range(9):
        trades.append(
            {
                "profit_loss": str(
                    100
                    if index < 7
                    else -100
                ),
                "profit_loss_percent": "1",
                "volatility_regime": (
                    "NORMAL"
                    if index < 7
                    else "HIGH"
                ),
                "atr_percent": str(
                    index + 1
                ),
            }
        )

    candidates = collect_shadow_candidates(
        trades,
        minimum_sample_size=30,
    )

    assert candidates

    assert (
        candidates[0]["trade_count"]
        >= candidates[-1]["trade_count"]
    )


def test_overlap_analyzer_detects_exact_duplicate():
    from research.shadow_edge_analyzer import (
        analyze_candidate_overlap,
    )

    trades = []

    values = [
        (100, 1, 1),
        (80, 2, 2),
        (-50, 3, 3),
        (-60, 4, 4),
        (-70, 5, 5),
        (-80, 6, 6),
    ]

    for profit, xic, xiu in values:
        trades.append(
            {
                "profit_loss": str(
                    profit
                ),
                "profit_loss_percent": "1",
                "rs_xic_20": str(xic),
                "rs_xiu_20": str(xiu),
            }
        )

    results = analyze_candidate_overlap(
        trades,
    )

    matches = [
        result
        for result in results
        if {
            result["left"]["factor"],
            result["right"]["factor"],
        }
        == {
            "rs_xic_20",
            "rs_xiu_20",
        }
    ]

    assert matches

    assert matches[
        0
    ]["relationship"] == (
        "EXACT_DUPLICATE"
    )

    assert matches[
        0
    ]["jaccard_percent"] == 100.0


def test_overlap_analyzer_detects_subset():
    from research.shadow_edge_analyzer import (
        analyze_candidate_overlap,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "volatility_regime": "NORMAL",
            "gap_percent": "6",
        },
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "volatility_regime": "NORMAL",
            "gap_percent": "5",
        },
        {
            "profit_loss": "80",
            "profit_loss_percent": "0.8",
            "volatility_regime": "NORMAL",
            "gap_percent": "2",
        },
        {
            "profit_loss": "70",
            "profit_loss_percent": "0.7",
            "volatility_regime": "NORMAL",
            "gap_percent": "1",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "volatility_regime": "HIGH",
            "gap_percent": "3",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "volatility_regime": "HIGH",
            "gap_percent": "4",
        },
    ]

    results = analyze_candidate_overlap(
        trades,
    )

    matches = [
        result
        for result in results
        if {
            result["left"]["factor"],
            result["right"]["factor"],
        }
        == {
            "volatility_regime",
            "gap_percent",
        }
        and (
            "SUBSET"
            in result["relationship"]
        )
    ]

    assert matches

    assert matches[
        0
    ]["shared_count"] == 2

    assert matches[
        0
    ][
        "smaller_overlap_percent"
    ] == 100.0


def test_cohort_analyzer_detects_concentration():
    from research.shadow_edge_analyzer import (
        analyze_candidate_cohort_concentration,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
            "entry_date": "2026-07-22",
            "exit_date": "2026-08-04",
        },
        {
            "profit_loss": "80",
            "profit_loss_percent": "0.8",
            "market_regime": "BULL",
            "entry_date": "2026-07-22",
            "exit_date": "2026-08-04",
        },
        {
            "profit_loss": "60",
            "profit_loss_percent": "0.6",
            "market_regime": "BULL",
            "entry_date": "2026-07-22",
            "exit_date": "2026-08-04",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-23",
            "exit_date": "2026-08-05",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-24",
            "exit_date": "2026-08-06",
        },
    ]

    results = (
        analyze_candidate_cohort_concentration(
            trades
        )
    )

    bull = [
        result
        for result in results
        if (
            result["factor"]
            == "market_regime"
            and result["value"]
            == "BULL"
        )
    ][0]

    assert (
        bull[
            "cohort_concentration_percent"
        ]
        == 100.0
    )

    assert (
        bull["concentration_status"]
        == "HIGH_ENTRY_EXIT_CONCENTRATION"
    )


def test_cohort_analyzer_allows_diverse_dates():
    from research.shadow_edge_analyzer import (
        analyze_candidate_cohort_concentration,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
            "entry_date": "2026-07-20",
            "exit_date": "2026-07-21",
        },
        {
            "profit_loss": "90",
            "profit_loss_percent": "0.9",
            "market_regime": "BULL",
            "entry_date": "2026-07-22",
            "exit_date": "2026-07-23",
        },
        {
            "profit_loss": "80",
            "profit_loss_percent": "0.8",
            "market_regime": "BULL",
            "entry_date": "2026-07-24",
            "exit_date": "2026-07-25",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-26",
            "exit_date": "2026-07-27",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-28",
            "exit_date": "2026-07-29",
        },
    ]

    results = (
        analyze_candidate_cohort_concentration(
            trades
        )
    )

    bull = [
        result
        for result in results
        if (
            result["factor"]
            == "market_regime"
            and result["value"]
            == "BULL"
        )
    ][0]

    assert (
        bull["concentration_status"]
        == "DIVERSE_COHORTS"
    )


def test_quality_gate_marks_duplicate_candidate_confounded():
    from research.shadow_edge_analyzer import (
        build_candidate_quality_gate,
    )

    trades = []

    for index in range(6):
        profit = (
            100
            if index < 2
            else -100
        )

        trades.append(
            {
                "profit_loss": str(
                    profit
                ),
                "profit_loss_percent": "1",
                "rs_xic_20": str(
                    index + 1
                ),
                "rs_xiu_20": str(
                    index + 1
                ),
                "entry_date": (
                    "2026-07-22"
                    if index < 2
                    else f"2026-07-{23 + index}"
                ),
                "exit_date": (
                    "2026-08-04"
                    if index < 2
                    else f"2026-08-{5 + index}"
                ),
            }
        )

    results = build_candidate_quality_gate(
        trades
    )

    target = [
        result
        for result in results
        if (
            result["factor"]
            == "rs_xic_20"
            and result["value"]
            == "LOW"
        )
    ][0]

    assert (
        target["exact_duplicate_count"]
        >= 1
    )

    assert (
        target["research_rating"]
        == "HEAVILY_CONFOUNDED"
    )


def test_quality_gate_marks_clean_small_sample_watch_only():
    from research.shadow_edge_analyzer import (
        build_candidate_quality_gate,
    )

    trades = [
        {
            "profit_loss": "100",
            "profit_loss_percent": "1",
            "market_regime": "BULL",
            "entry_date": "2026-07-10",
            "exit_date": "2026-07-11",
        },
        {
            "profit_loss": "80",
            "profit_loss_percent": "0.8",
            "market_regime": "BULL",
            "entry_date": "2026-07-14",
            "exit_date": "2026-07-15",
        },
        {
            "profit_loss": "60",
            "profit_loss_percent": "0.6",
            "market_regime": "BULL",
            "entry_date": "2026-07-18",
            "exit_date": "2026-07-19",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-20",
            "exit_date": "2026-07-21",
        },
        {
            "profit_loss": "-100",
            "profit_loss_percent": "-1",
            "market_regime": "BEAR",
            "entry_date": "2026-07-22",
            "exit_date": "2026-07-23",
        },
    ]

    results = build_candidate_quality_gate(
        trades
    )

    target = [
        result
        for result in results
        if (
            result["factor"]
            == "market_regime"
            and result["value"]
            == "BULL"
        )
    ][0]

    assert (
        target["research_rating"]
        == "WATCH_ONLY"
    )

    assert (
        target["exact_duplicate_count"]
        == 0
    )

    assert (
        target["cohort_status"]
        == "DIVERSE_COHORTS"
    )


def test_quality_gate_does_not_penalize_broad_candidate_for_one_sided_overlap():
    from research.shadow_edge_analyzer import (
        build_candidate_quality_gate,
    )

    profits = [
        100,
        100,
        50,
        50,
        50,
        50,
        50,
        -10,
        -200,
    ]

    sma_values = [
        4,
        5,
        1,
        2,
        3,
        7,
        8,
        6,
        9,
    ]

    trades = []

    for index in range(9):
        trades.append(
            {
                "profit_loss": str(
                    profits[index]
                ),
                "profit_loss_percent": "1",
                "volatility_regime": (
                    "NORMAL"
                    if index < 7
                    else "HIGH"
                ),
                "ma_close_vs_sma200_percent": str(
                    sma_values[index]
                ),
                "entry_date": (
                    f"2026-07-{10 + index:02d}"
                ),
                "exit_date": (
                    f"2026-07-{11 + index:02d}"
                ),
            }
        )

    results = build_candidate_quality_gate(
        trades
    )

    normal = [
        result
        for result in results
        if (
            result["factor"]
            == "volatility_regime"
            and result["value"]
            == "NORMAL"
        )
    ][0]

    assert (
        normal["high_overlap_count"]
        >= 1
    )

    assert (
        normal[
            "material_high_overlap_count"
        ]
        == 0
    )

    assert (
        normal["research_rating"]
        == "WATCH_ONLY"
    )
