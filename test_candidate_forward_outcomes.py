import csv
from datetime import (
    datetime,
    timezone,
)

import pandas as pd

from research.candidate_forward_outcomes import (
    calculate_candidate_forward_outcomes,
    load_candidate_snapshot_rows,
    save_candidate_forward_outcomes,
)


def make_candidate():
    return {
        "strategy": "MOMENTUM",
        "signal_date": "2026-08-18",
        "symbol": "TEST.TO",
        "decision": "WATCH",
        "close": 100.0,
        "tmqs": 72.0,
        "rvol": 1.3,
        "reason": "Developing setup",
        "data_source": "YAHOO_DAILY_EOD",
    }


def make_history(periods=20):
    dates = pd.bdate_range(
        start="2026-08-19",
        periods=periods,
    )

    rows = []

    for index, bar_date in enumerate(
        dates,
        start=1,
    ):
        rows.append(
            {
                "date": bar_date,
                "open": 100.0 + index,
                "high": 101.0 + index,
                "low": 99.0 - index,
                "close": 100.0 + index,
                "volume": 1_000_000,
            }
        )

    frame = pd.DataFrame(rows)

    frame.attrs[
        "data_source"
    ] = "IBKR"

    frame.attrs[
        "historical_data_type"
    ] = "TRADES"

    return frame


def test_forward_horizons_use_actual_trading_bars():
    history = make_history()

    row = calculate_candidate_forward_outcomes(
        make_candidate(),
        history,
        as_of_date="2026-09-30",
        captured_at=datetime(
            2026,
            9,
            30,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert row["outcome_status"] == "COMPLETE"

    assert (
        row["completed_horizon_count"]
        == 6
    )

    assert row["h1_date"] == "2026-08-19"
    assert row["h1_close"] == 101.0
    assert row["h1_return_percent"] == 1.0

    assert (
        row[
            "h1_max_high_return_percent"
        ]
        == 2.0
    )

    assert (
        row[
            "h1_min_low_return_percent"
        ]
        == -2.0
    )

    assert row["h3_date"] == "2026-08-21"
    assert row["h3_close"] == 103.0
    assert row["h3_return_percent"] == 3.0

    assert (
        row[
            "h3_max_high_return_percent"
        ]
        == 4.0
    )

    assert (
        row[
            "h3_min_low_return_percent"
        ]
        == -4.0
    )

    assert row["h20_return_percent"] == 20.0

    assert row["outcome_data_source"] == "IBKR"

    assert (
        row["historical_data_type"]
        == "TRADES"
    )


def test_as_of_date_prevents_future_leakage():
    history = make_history()

    row = calculate_candidate_forward_outcomes(
        make_candidate(),
        history,
        as_of_date="2026-08-20",
    )

    assert row["outcome_status"] == "PARTIAL"

    assert (
        row["available_trading_days"]
        == 2
    )

    assert (
        row["completed_horizon_count"]
        == 2
    )

    assert row["h1_date"] == "2026-08-19"
    assert row["h2_date"] == "2026-08-20"
    assert row["h3_date"] == ""
    assert row["h5_close"] == ""


def test_no_future_bar_is_pending_not_error():
    history = make_history()

    row = calculate_candidate_forward_outcomes(
        make_candidate(),
        history,
        as_of_date="2026-08-18",
    )

    assert row["outcome_status"] == "PENDING"

    assert (
        row["completed_horizon_count"]
        == 0
    )

    assert row["outcome_error"] == ""


def test_snapshot_loader_unifies_all_three_strategies(
    tmp_path,
):
    fixtures = [
        (
            "research/momentum_results",
            "MOMENTUM",
            {
                "signal_date": "2026-08-18",
                "symbol": "AAA.TO",
                "decision": "READY",
                "close": "100",
                "tmqs": "85",
                "rvol": "1.8",
                "data_source": "YAHOO_DAILY_EOD",
            },
        ),
        (
            "research/52_week_results",
            "52_WEEK_BREAKOUT",
            {
                "signal_date": "2026-08-18",
                "symbol": "BBB.TO",
                "decision": "WATCH",
                "close": "50",
                "tmqs": "70",
                "rvol": "1.2",
                "live_data_source": "IBKR",
                "price_source": "LAST",
            },
        ),
        (
            "research/mean_reversion_results",
            "MEAN_REVERSION",
            {
                "signal_date": "2026-08-18",
                "symbol": "CCC.TO",
                "decision": "IGNORE",
                "close": "25",
                "tmqs": "40",
                "rvol": "0.8",
                "live_data_source": "IBKR",
                "price_source": "LAST",
            },
        ),
    ]

    for (
        relative_directory,
        strategy,
        row,
    ) in fixtures:
        directory = (
            tmp_path
            / relative_directory
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            directory
            / "2026-08-18.csv"
        )

        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(
                    row.keys()
                ),
            )

            writer.writeheader()
            writer.writerow(row)

    candidates = (
        load_candidate_snapshot_rows(
            root_directory=tmp_path
        )
    )

    assert len(candidates) == 3

    assert {
        row["strategy"]
        for row in candidates
    } == {
        "MOMENTUM",
        "52_WEEK_BREAKOUT",
        "MEAN_REVERSION",
    }

    by_symbol = {
        row["symbol"]: row
        for row in candidates
    }

    assert (
        by_symbol["AAA.TO"][
            "signal_data_source"
        ]
        == "YAHOO_DAILY_EOD"
    )

    assert (
        by_symbol["BBB.TO"][
            "signal_data_source"
        ]
        == "IBKR"
    )

    assert (
        by_symbol["CCC.TO"][
            "signal_price"
        ]
        == 25.0
    )


def test_forward_outcome_table_saves_atomically(
    tmp_path,
):
    row = calculate_candidate_forward_outcomes(
        make_candidate(),
        make_history(),
        as_of_date="2026-09-30",
    )

    output_path = (
        tmp_path
        / "candidate_forward_outcomes.csv"
    )

    result = save_candidate_forward_outcomes(
        [row],
        output_path=output_path,
    )

    assert result["success"] is True
    assert result["rows_saved"] == 1

    assert output_path.exists()

    assert not (
        tmp_path
        / "candidate_forward_outcomes.csv.tmp"
    ).exists()

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        saved = next(
            csv.DictReader(file)
        )

    assert saved["symbol"] == "TEST.TO"
    assert saved["decision"] == "WATCH"

    assert (
        saved["outcome_status"]
        == "COMPLETE"
    )

    assert saved["h10_return_percent"] == "10.0"
