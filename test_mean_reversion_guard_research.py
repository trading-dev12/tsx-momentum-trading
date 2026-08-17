import csv
from datetime import (
    datetime,
    timezone,
)

import paper_trading.automatic_eod as automatic_eod

from research.mean_reversion_guard_research import (
    build_mean_reversion_guard_rows,
    save_mean_reversion_guard_research,
)


def raw_results():
    return {
        "ready": [
            {
                "symbol": "READY.TO",
                "strategy": "MEAN_REVERSION",
                "signal_date": "2026-08-18",
                "close": 100.0,
                "tmqs": 81.0,
                "rvol": 1.1,
                "decision": "READY",
                "reason": "Raw READY",
            }
        ],
        "watch": [
            {
                "symbol": "WATCH.TO",
                "strategy": "MEAN_REVERSION",
                "signal_date": "2026-08-18",
                "close": 50.0,
                "tmqs": 60.0,
                "rvol": 0.9,
                "decision": "WATCH",
                "reason": "Raw WATCH",
            }
        ],
        "ignore": [],
        "errors": [],
    }


def blocked_guard():
    return {
        "guard": {
            "allow_new_entries": False,
            "guard_status": "BLOCKED",
            "market_regime": "BEAR",
            "reason": (
                "Broad TSX market regime is BEAR."
            ),
        },
        "queue_results": {
            "ready": [],
            "watch": [],
            "ignore": [],
            "errors": [],
        },
        "blocked_ready_count": 1,
        "blocked_ready": [],
    }


def test_guard_rows_preserve_raw_and_queue_decisions():
    rows = build_mean_reversion_guard_rows(
        raw_results(),
        blocked_guard(),
        measurement_date="2026-08-18",
        captured_at=datetime(
            2026,
            8,
            18,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    by_symbol = {
        row["symbol"]: row
        for row in rows
    }

    ready = by_symbol[
        "READY.TO"
    ]

    assert (
        ready["raw_decision"]
        == "READY"
    )

    assert (
        ready[
            "queue_decision_after_guard"
        ]
        == "WATCH"
    )

    assert (
        ready[
            "guard_blocked_ready"
        ]
        is True
    )

    assert (
        ready[
            "queue_eligible_after_guard"
        ]
        is False
    )

    assert (
        ready["market_regime"]
        == "BEAR"
    )

    watch = by_symbol[
        "WATCH.TO"
    ]

    assert (
        watch["raw_decision"]
        == "WATCH"
    )

    assert (
        watch[
            "queue_decision_after_guard"
        ]
        == "WATCH"
    )

    assert (
        watch[
            "guard_applicable_to_candidate"
        ]
        is False
    )

    assert (
        watch[
            "guard_blocked_ready"
        ]
        is False
    )


def test_guard_research_saves_daily_csv_atomically(
    tmp_path,
):
    result = (
        save_mean_reversion_guard_research(
            raw_results=raw_results(),
            guarded_result=blocked_guard(),
            measurement_date=(
                "2026-08-18"
            ),
            output_directory=(
                tmp_path
            ),
        )
    )

    assert result["success"] is True
    assert result["rows_saved"] == 2

    assert (
        result[
            "blocked_ready_count"
        ]
        == 1
    )

    path = (
        tmp_path
        / "2026-08-18.csv"
    )

    assert path.exists()

    assert not (
        tmp_path
        / "2026-08-18.csv.tmp"
    ).exists()

    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 2

    ready = next(
        row
        for row in rows
        if row["symbol"]
        == "READY.TO"
    )

    assert (
        ready["raw_decision"]
        == "READY"
    )

    assert (
        ready[
            "queue_decision_after_guard"
        ]
        == "WATCH"
    )

    assert (
        ready["market_guard_status"]
        == "BLOCKED"
    )

    assert (
        ready["market_regime"]
        == "BEAR"
    )

    assert (
        ready["guard_blocked_ready"]
        == "True"
    )


def test_shadow_scan_records_guard_research_fail_soft(
    monkeypatch,
):
    raw = raw_results()

    class Pending:
        def get_all(self):
            return []

    class Engine:
        pending_trades = Pending()

        def queue_eod_signals(
            self,
            results,
        ):
            return {
                "attempted": 0,
                "added": 0,
                "rejected": 0,
                "already_open": 0,
                "already_pending": 0,
                "other_rejected": 0,
                "results": [],
            }

    monkeypatch.setattr(
        automatic_eod,
        "load_all_watchlists",
        lambda: ["READY.TO"],
    )

    monkeypatch.setattr(
        automatic_eod,
        "scan_mean_reversion",
        lambda watchlist, measurement_date=None: raw,
    )

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_results",
        lambda results, measurement_date=None: (
            "raw.csv"
        ),
    )

    captured = {}

    def fake_guard_save(
        **kwargs,
    ):
        captured.update(
            kwargs
        )

        return {
            "success": True,
            "status": "SAVED",
            "report_path": "guard.csv",
            "rows_saved": 2,
            "blocked_ready_count": 1,
        }

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_guard_research",
        fake_guard_save,
    )

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=Engine(),
            measurement_date=(
                "2026-08-18"
            ),
            market_regime_provider=lambda date: {
                "status": "AVAILABLE",
                "regime": "BEAR",
            },
        )
    )

    assert (
        captured["raw_results"]
        is raw
    )

    assert (
        captured["measurement_date"]
        == "2026-08-18"
    )

    assert (
        captured["guarded_result"][
            "guard"
        ][
            "market_regime"
        ]
        == "BEAR"
    )

    assert (
        result[
            "market_guard_research"
        ][
            "status"
        ]
        == "SAVED"
    )


def test_guard_research_failure_cannot_break_queue(
    monkeypatch,
):
    raw = raw_results()

    class Pending:
        def get_all(self):
            return []

    class Engine:
        pending_trades = Pending()

        def queue_eod_signals(
            self,
            results,
        ):
            return {
                "attempted": len(
                    results["ready"]
                ),
                "added": len(
                    results["ready"]
                ),
                "rejected": 0,
                "already_open": 0,
                "already_pending": 0,
                "other_rejected": 0,
                "results": [],
            }

    monkeypatch.setattr(
        automatic_eod,
        "load_all_watchlists",
        lambda: ["READY.TO"],
    )

    monkeypatch.setattr(
        automatic_eod,
        "scan_mean_reversion",
        lambda watchlist, measurement_date=None: raw,
    )

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_results",
        lambda results, measurement_date=None: (
            "raw.csv"
        ),
    )

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_guard_research",
        lambda **kwargs: (
            (_ for _ in ()).throw(
                OSError(
                    "Simulated research write failure"
                )
            )
        ),
    )

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=Engine(),
            measurement_date=(
                "2026-08-18"
            ),
            market_regime_provider=lambda date: {
                "status": "AVAILABLE",
                "regime": "BULL",
            },
        )
    )

    # Trading path still operates normally.
    assert result["queue_ready"] == 1
    assert result["queued"] == 1

    # Research failure is visible but fail-soft.
    assert (
        result[
            "market_guard_research"
        ][
            "status"
        ]
        == "ERROR"
    )
