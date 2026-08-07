from datetime import datetime

from paper_trading.automatic_eod import (
    run_automatic_eod_cycle,
    should_run_automatic_eod,
)


class FakePaperEngine:
    def queue_eod_signals(self, results):
        return {
            "added": len(results["ready"]),
            "rejected": 0,
        }


def fake_scan_provider(current_datetime=None):
    return {
        "ready": [
            {"symbol": "TEST1.TO"},
            {"symbol": "TEST2.TO"},
        ],
        "watch": [
            {"symbol": "WATCH.TO"},
        ],
        "ignore": [],
        "errors": [],
    }


def fake_validation_runner(state_file=None):
    return {
        "success": True,
        "status": "PASS",
        "report_path": "validation_reports/test_report.json",
        "message": "Validation completed successfully.",
    }


def fake_shadow_scan_runner():
    return {
        "success": True,
        "ready": 1,
        "watch": 2,
        "ignored": 50,
        "errors": 0,
        "report_path": "research/52_week_results/test.csv",
    }


def fake_mean_reversion_runner(paper_engine=None):
    return {
        "success": True,
        "ready": 0,
        "watch": 1,
        "ignored": 52,
        "errors": 0,
        "queued": 0,
        "duplicates": 0,
        "report_path": (
            "research/mean_reversion_results/test.csv"
        ),
    }


def test_automatic_eod_validation(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "paper_trading.automatic_eod.send_telegram_message",
        lambda message: {
            "success": True,
            "message": "Telegram mocked during test.",
        },
    )

    state_file = tmp_path / "automatic_eod_state.json"

    summary = run_automatic_eod_cycle(
        paper_engine=FakePaperEngine(),
        current_datetime=datetime(
            2026,
            7,
            16,
            17,
            0,
        ),
        state_file=str(state_file),
        scan_provider=fake_scan_provider,
        validation_runner=fake_validation_runner,
        shadow_scan_runner=fake_shadow_scan_runner,
        mean_reversion_runner=(
            fake_mean_reversion_runner
        ),
    )

    assert summary["status"] == "COMPLETED"
    assert summary["ready"] == 2
    assert summary["watch"] == 1
    assert summary["ignored"] == 0
    assert summary["queued"] == 2
    assert summary["validation"]["status"] == "PASS"
    assert (
        summary["breakout_52week_shadow"]["ready"]
        == 1
    )


def test_automatic_eod_not_due_before_405(tmp_path):
    state_file = tmp_path / "automatic_eod_state.json"

    should_run = should_run_automatic_eod(
        current_datetime=datetime(
            2026,
            7,
            16,
            16,
            4,
        ),
        state_file=str(state_file),
    )

    assert should_run is False


def test_automatic_eod_due_at_405(tmp_path):
    state_file = tmp_path / "automatic_eod_state.json"

    should_run = should_run_automatic_eod(
        current_datetime=datetime(
            2026,
            7,
            16,
            16,
            5,
        ),
        state_file=str(state_file),
    )

    assert should_run is True

def test_automatic_eod_not_due_before_early_close_plus_5(
    tmp_path,
):
    state_file = (
        tmp_path / "automatic_eod_state.json"
    )

    should_run = should_run_automatic_eod(
        current_datetime=datetime(
            2026,
            12,
            24,
            13,
            4,
        ),
        state_file=str(state_file),
    )

    assert should_run is False


def test_automatic_eod_due_at_early_close_plus_5(
    tmp_path,
):
    state_file = (
        tmp_path / "automatic_eod_state.json"
    )

    should_run = should_run_automatic_eod(
        current_datetime=datetime(
            2026,
            12,
            24,
            13,
            5,
        ),
        state_file=str(state_file),
    )

    assert should_run is True