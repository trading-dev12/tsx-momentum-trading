from datetime import datetime

import paper_trading.automatic_eod as eod_module
from core.market_hours import TORONTO_TIMEZONE


class OneCycleStopEvent:
    def __init__(self):
        self.check_count = 0

    def is_set(self):
        self.check_count += 1

        return self.check_count > 1

    def wait(self, seconds):
        return None


def test_worker_recovers_friday_eod_monday_premarket(
    monkeypatch,
):
    monday_premarket = datetime(
        2026,
        8,
        10,
        8,
        0,
        tzinfo=TORONTO_TIMEZONE,
    )

    monkeypatch.setattr(
        eod_module,
        "normalize_current_datetime",
        lambda: monday_premarket,
    )

    monkeypatch.setattr(
        eod_module,
        "load_last_run_date",
        lambda: "2026-08-06",
    )

    cycle_datetimes = []

    def fake_cycle(**kwargs):
        cycle_datetimes.append(
            kwargs["current_datetime"]
        )

        return {
            "success": True,
            "status": "COMPLETED",
        }

    monkeypatch.setattr(
        eod_module,
        "run_automatic_eod_cycle",
        fake_cycle,
    )

    eod_module.automatic_eod_worker(
        paper_engine=object(),
        stop_event=OneCycleStopEvent(),
    )

    assert len(cycle_datetimes) == 1

    recovered_datetime = (
        cycle_datetimes[0]
    )

    assert (
        recovered_datetime.date().isoformat()
        == "2026-08-07"
    )

    assert recovered_datetime.hour == 16
    assert recovered_datetime.minute == 5


def test_worker_does_not_recover_after_market_open(
    monkeypatch,
):
    monday_open = datetime(
        2026,
        8,
        10,
        9,
        30,
        tzinfo=TORONTO_TIMEZONE,
    )

    monkeypatch.setattr(
        eod_module,
        "normalize_current_datetime",
        lambda: monday_open,
    )

    monkeypatch.setattr(
        eod_module,
        "load_last_run_date",
        lambda: "2026-08-06",
    )

    cycle_datetimes = []

    def fake_cycle(**kwargs):
        cycle_datetimes.append(
            kwargs["current_datetime"]
        )

        return {
            "success": True,
            "status": "NOT_DUE",
        }

    monkeypatch.setattr(
        eod_module,
        "run_automatic_eod_cycle",
        fake_cycle,
    )

    eod_module.automatic_eod_worker(
        paper_engine=object(),
        stop_event=OneCycleStopEvent(),
    )

    assert len(cycle_datetimes) == 1

    assert cycle_datetimes[0] == monday_open