from datetime import datetime

import paper_trading.automatic_eod as eod_module
import paper_trading.signal_journal as signal_journal

from core.market_hours import TORONTO_TIMEZONE


class FakePaperEngine:
    def queue_eod_signals(
        self,
        results,
    ):
        return {
            "added": len(
                results.get(
                    "ready",
                    [],
                )
            ),
            "rejected": 0,
        }


class OneCycleStopEvent:
    def __init__(self):
        self.check_count = 0

    def is_set(self):
        self.check_count += 1

        return self.check_count > 1

    def wait(
        self,
        seconds,
    ):
        return None


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
        "message": "Test validation passed.",
    }


def fake_breakout_runner(
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
        "report_path": None,
    }


def install_safe_eod_mocks(
    monkeypatch,
):
    monkeypatch.setattr(
        eod_module,
        "send_telegram_message",
        lambda message: {
            "success": True,
            "message": "Telegram mocked.",
        },
    )

    monkeypatch.setattr(
        eod_module,
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
        signal_journal,
        "record_ready_signals",
        lambda *args, **kwargs: None,
    )


def test_normal_eod_passes_trading_date_to_mean_reversion(
    tmp_path,
    monkeypatch,
):
    install_safe_eod_mocks(
        monkeypatch
    )

    measurement_dates = []

    def fake_mean_reversion_runner(
        paper_engine=None,
        measurement_date=None,
    ):
        measurement_dates.append(
            measurement_date
        )

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
            "report_path": None,
        }

    state_file = (
        tmp_path
        / "automatic_eod_state.json"
    )

    result = (
        eod_module
        .run_automatic_eod_cycle(
            paper_engine=FakePaperEngine(),
            current_datetime=datetime(
                2026,
                8,
                13,
                17,
                0,
                tzinfo=TORONTO_TIMEZONE,
            ),
            state_file=str(
                state_file
            ),
            scan_provider=(
                fake_scan_provider
            ),
            validation_runner=(
                fake_validation_runner
            ),
            shadow_scan_runner=(
                fake_breakout_runner
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

    assert measurement_dates == [
        "2026-08-13"
    ]


def test_recovered_eod_passes_original_trading_date(
    tmp_path,
    monkeypatch,
):
    install_safe_eod_mocks(
        monkeypatch
    )

    monday_premarket = datetime(
        2026,
        8,
        10,
        8,
        0,
        tzinfo=TORONTO_TIMEZONE,
    )

    def fake_normalize(
        value=None,
    ):
        if value is None:
            return monday_premarket

        if value.tzinfo is None:
            return value.replace(
                tzinfo=TORONTO_TIMEZONE
            )

        return value

    monkeypatch.setattr(
        eod_module,
        "normalize_current_datetime",
        fake_normalize,
    )

    monkeypatch.setattr(
        eod_module,
        "load_last_run_date",
        lambda state_file=None: (
            "2026-08-06"
        ),
    )

    measurement_dates = []

    def fake_mean_reversion_runner(
        paper_engine=None,
        measurement_date=None,
    ):
        measurement_dates.append(
            measurement_date
        )

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
            "report_path": None,
        }

    actual_cycle = (
        eod_module
        .run_automatic_eod_cycle
    )

    state_file = (
        tmp_path
        / "recovery_eod_state.json"
    )

    def wrapped_cycle(**kwargs):
        return actual_cycle(
            **kwargs,
            state_file=str(
                state_file
            ),
            scan_provider=(
                fake_scan_provider
            ),
            validation_runner=(
                fake_validation_runner
            ),
            shadow_scan_runner=(
                fake_breakout_runner
            ),
            mean_reversion_runner=(
                fake_mean_reversion_runner
            ),
        )

    monkeypatch.setattr(
        eod_module,
        "run_automatic_eod_cycle",
        wrapped_cycle,
    )

    eod_module.automatic_eod_worker(
        paper_engine=FakePaperEngine(),
        stop_event=OneCycleStopEvent(),
    )

    # Monday morning recovery is for
    # Friday August 7, not Monday August 10.
    assert measurement_dates == [
        "2026-08-07"
    ]
