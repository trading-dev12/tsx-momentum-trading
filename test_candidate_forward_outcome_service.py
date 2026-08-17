from datetime import (
    datetime,
    timezone,
)

import pandas as pd

from research.candidate_forward_outcomes import (
    calculate_candidate_forward_outcomes,
    save_candidate_forward_outcomes,
)
from research.candidate_forward_outcome_service import (
    run_candidate_forward_outcome_refresh,
)


def candidate(
    symbol="AAA.TO",
    strategy="MOMENTUM",
    signal_date="2026-08-18",
    decision="WATCH",
):
    return {
        "strategy": strategy,
        "signal_date": signal_date,
        "symbol": symbol,
        "decision": decision,
        "close": 100.0,
        "tmqs": 70.0,
        "rvol": 1.2,
        "reason": "Test candidate",
        "data_source": (
            "YAHOO_DAILY_EOD"
        ),
    }


def history(
    start="2026-08-19",
    periods=30,
):
    dates = pd.bdate_range(
        start=start,
        periods=periods,
    )

    frame = pd.DataFrame(
        [
            {
                "date": bar_date,
                "open": (
                    100.0 + index
                ),
                "high": (
                    101.0 + index
                ),
                "low": (
                    99.0 + index
                ),
                "close": (
                    100.0 + index
                ),
                "volume": 1_000_000,
            }
            for index, bar_date
            in enumerate(
                dates,
                start=1,
            )
        ]
    )

    frame.attrs[
        "data_source"
    ] = "IBKR"

    frame.attrs[
        "historical_data_type"
    ] = "TRADES"

    return frame


def test_one_ibkr_request_updates_all_candidates_for_symbol(
    tmp_path,
):
    candidates = [
        candidate(
            symbol="AAA.TO",
            strategy="MOMENTUM",
        ),
        candidate(
            symbol="AAA.TO",
            strategy=(
                "52_WEEK_BREAKOUT"
            ),
        ),
    ]

    calls = []

    fake_provider = object()

    def fake_history_loader(
        **kwargs,
    ):
        calls.append(
            kwargs
        )

        return history()

    result = (
        run_candidate_forward_outcome_refresh(
            as_of_date="2026-09-30",
            output_path=(
                tmp_path
                / "outcomes.csv"
            ),
            candidate_loader=(
                lambda root_directory: (
                    candidates
                )
            ),
            history_loader=(
                fake_history_loader
            ),
            provider=fake_provider,
            captured_at=datetime(
                2026,
                9,
                30,
                20,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    assert result["success"] is True

    assert (
        result["symbols_requested"]
        == 1
    )

    assert (
        result[
            "refreshed_candidates"
        ]
        == 2
    )

    assert len(calls) == 1

    assert (
        calls[0]["symbol"]
        == "AAA.TO"
    )

    assert (
        calls[0][
            "measurement_date"
        ]
        == "2026-09-30"
    )

    assert (
        calls[0]["adjusted"]
        is False
    )

    assert (
        calls[0]["provider"]
        is fake_provider
    )

    assert (
        result["status_counts"][
            "COMPLETE"
        ]
        == 2
    )


def test_complete_candidate_is_not_downloaded_again(
    tmp_path,
):
    item = candidate()

    existing = (
        calculate_candidate_forward_outcomes(
            item,
            history(),
            as_of_date="2026-09-30",
        )
    )

    output_path = (
        tmp_path
        / "outcomes.csv"
    )

    save_candidate_forward_outcomes(
        [existing],
        output_path=output_path,
    )

    def forbidden_history_loader(
        **kwargs,
    ):
        raise AssertionError(
            "COMPLETE candidate must not "
            "request IBKR history again."
        )

    result = (
        run_candidate_forward_outcome_refresh(
            as_of_date="2026-10-01",
            output_path=output_path,
            candidate_loader=(
                lambda root_directory: [
                    item
                ]
            ),
            history_loader=(
                forbidden_history_loader
            ),
            provider=object(),
        )
    )

    assert (
        result["symbols_requested"]
        == 0
    )

    assert (
        result["complete_preserved"]
        == 1
    )

    assert (
        result["status_counts"][
            "COMPLETE"
        ]
        == 1
    )


def test_same_day_candidate_does_not_consume_ibkr_request(
    tmp_path,
):
    item = candidate(
        signal_date="2026-08-18",
    )

    def forbidden_history_loader(
        **kwargs,
    ):
        raise AssertionError(
            "Same-day candidate cannot "
            "have a future bar yet."
        )

    result = (
        run_candidate_forward_outcome_refresh(
            as_of_date="2026-08-18",
            output_path=(
                tmp_path
                / "outcomes.csv"
            ),
            candidate_loader=(
                lambda root_directory: [
                    item
                ]
            ),
            history_loader=(
                forbidden_history_loader
            ),
            provider=object(),
        )
    )

    assert (
        result["symbols_requested"]
        == 0
    )

    assert (
        result["same_day_pending"]
        == 1
    )

    assert (
        result["status_counts"][
            "PENDING"
        ]
        == 1
    )


def test_symbol_budget_prioritizes_oldest_incomplete_candidates(
    tmp_path,
):
    candidates = [
        candidate(
            symbol="CCC.TO",
            signal_date="2026-08-03",
        ),
        candidate(
            symbol="AAA.TO",
            signal_date="2026-08-01",
        ),
        candidate(
            symbol="BBB.TO",
            signal_date="2026-08-02",
        ),
    ]

    requested = []

    def fake_history_loader(
        **kwargs,
    ):
        requested.append(
            kwargs["symbol"]
        )

        return history(
            start="2026-08-04",
            periods=30,
        )

    result = (
        run_candidate_forward_outcome_refresh(
            as_of_date="2026-09-30",
            output_path=(
                tmp_path
                / "outcomes.csv"
            ),
            max_symbols_per_run=2,
            candidate_loader=(
                lambda root_directory: (
                    candidates
                )
            ),
            history_loader=(
                fake_history_loader
            ),
            provider=object(),
        )
    )

    assert requested == [
        "AAA.TO",
        "BBB.TO",
    ]

    assert (
        result["symbols_requested"]
        == 2
    )

    assert (
        result["symbols_deferred"]
        == 1
    )

    assert (
        result["status"]
        == "PARTIAL"
    )
