from datetime import datetime

import paper_trading.automatic_eod as automatic_eod


class FakePaperEngine:
    def queue_eod_signals(
        self,
        results,
    ):
        return {
            "added": len(
                results["ready"]
            ),
            "rejected": 0,
        }


def fake_scan_provider(
    current_datetime=None,
):
    return {
        "ready": [],
        "watch": [],
        "ignore": [],
        "errors": [],
    }


def fake_validation_runner(
    state_file=None,
):
    return {
        "success": True,
        "status": "PASS",
        "report_path": None,
        "message": (
            "Validation completed."
        ),
    }


def fake_shadow_runner(
    paper_engine=None,
):
    return {
        "success": True,
        "ready": 0,
        "watch": 0,
        "ignored": 0,
        "errors": 0,
        "queued": 0,
        "already_open": 0,
        "already_pending": 0,
        "other_rejected": 0,
        "pending_total": 0,
    }


def fake_mean_reversion_runner(
    paper_engine=None,
    measurement_date=None,
):
    return {
        "success": True,
        "ready": 0,
        "watch": 0,
        "ignored": 0,
        "errors": 0,
        "queued": 0,
        "already_open": 0,
        "already_pending": 0,
        "other_rejected": 0,
        "pending_total": 0,
        "queue_ready": 0,
        "market_guard_blocked": 0,
        "market_guard": {
            "guard_status": "PASS",
            "market_regime": "BULL",
        },
    }


def _prepare_safe_eod_test(
    monkeypatch,
):
    monkeypatch.setattr(
        automatic_eod,
        "send_telegram_message",
        lambda message: {
            "success": True,
            "message": "mocked",
        },
    )

    monkeypatch.setattr(
        automatic_eod,
        "create_backup",
        lambda: {
            "success": True,
            "enabled": True,
            "backup_path": "test",
            "copied": 0,
            "skipped": 0,
            "errors": [],
        },
    )

    monkeypatch.setattr(
        "paper_trading.signal_journal.record_ready_signals",
        lambda *args, **kwargs: None,
    )


def test_eod_runs_candidate_history_capture(
    tmp_path,
    monkeypatch,
):
    _prepare_safe_eod_test(
        monkeypatch
    )

    calls = []

    def fake_candidate_history_runner():
        calls.append(
            "candidate_history"
        )

        return {
            "success": True,
            "strategies": {
                "Momentum": {
                    "success": True,
                    "saved": True,
                },
                "52-Week Breakout": {
                    "success": True,
                    "saved": True,
                },
                "Mean Reversion": {
                    "success": True,
                    "saved": True,
                },
            },
        }

    result = (
        automatic_eod
        .run_automatic_eod_cycle(
            paper_engine=FakePaperEngine(),
            current_datetime=datetime(
                2026,
                8,
                14,
                16,
                10,
            ),
            state_file=str(
                tmp_path
                / "automatic_eod_state.json"
            ),
            scan_provider=(
                fake_scan_provider
            ),
            validation_runner=(
                fake_validation_runner
            ),
            shadow_scan_runner=(
                fake_shadow_runner
            ),
            mean_reversion_runner=(
                fake_mean_reversion_runner
            ),
            candidate_history_runner=(
                fake_candidate_history_runner
            ),
        )
    )

    assert (
        result["status"]
        == "COMPLETED"
    )

    assert calls == [
        "candidate_history"
    ]

    assert (
        result["candidate_history"][
            "success"
        ]
        is True
    )


def test_candidate_history_failure_does_not_fail_eod(
    tmp_path,
    monkeypatch,
):
    _prepare_safe_eod_test(
        monkeypatch
    )

    def failing_candidate_history_runner():
        raise RuntimeError(
            "simulated research failure"
        )

    result = (
        automatic_eod
        .run_automatic_eod_cycle(
            paper_engine=FakePaperEngine(),
            current_datetime=datetime(
                2026,
                8,
                14,
                16,
                10,
            ),
            state_file=str(
                tmp_path
                / "automatic_eod_state.json"
            ),
            scan_provider=(
                fake_scan_provider
            ),
            validation_runner=(
                fake_validation_runner
            ),
            shadow_scan_runner=(
                fake_shadow_runner
            ),
            mean_reversion_runner=(
                fake_mean_reversion_runner
            ),
            candidate_history_runner=(
                failing_candidate_history_runner
            ),
        )
    )

    assert (
        result["status"]
        == "COMPLETED"
    )

    assert result["success"] is True

    assert (
        result["candidate_history"][
            "success"
        ]
        is False
    )

    assert (
        result["candidate_history"][
            "status"
        ]
        == "ERROR"
    )

    assert (
        "simulated research failure"
        in result[
            "candidate_history"
        ]["message"]
    )


def test_eod_without_history_runner_remains_compatible(
    tmp_path,
    monkeypatch,
):
    _prepare_safe_eod_test(
        monkeypatch
    )

    result = (
        automatic_eod
        .run_automatic_eod_cycle(
            paper_engine=FakePaperEngine(),
            current_datetime=datetime(
                2026,
                8,
                14,
                16,
                10,
            ),
            state_file=str(
                tmp_path
                / "automatic_eod_state.json"
            ),
            scan_provider=(
                fake_scan_provider
            ),
            validation_runner=(
                fake_validation_runner
            ),
            shadow_scan_runner=(
                fake_shadow_runner
            ),
            mean_reversion_runner=(
                fake_mean_reversion_runner
            ),
        )
    )

    assert (
        result["status"]
        == "COMPLETED"
    )

    assert (
        result["candidate_history"][
            "status"
        ]
        == "NOT_REQUESTED"
    )
