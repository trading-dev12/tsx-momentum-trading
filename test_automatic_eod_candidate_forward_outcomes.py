from datetime import datetime

import paper_trading.automatic_eod as eod


def test_forward_outcome_capture_uses_authoritative_eod_date():
    calls = []

    def runner(**kwargs):
        calls.append(
            kwargs
        )

        return {
            "success": True,
            "status": "UPDATED",
            "as_of_date": kwargs[
                "as_of_date"
            ],
        }

    result = (
        eod.run_forward_outcome_research_capture(
            runner=runner,
            current_date="2026-08-18",
        )
    )

    assert result["success"] is True
    assert result["status"] == "UPDATED"

    assert calls == [
        {
            "as_of_date": (
                "2026-08-18"
            )
        }
    ]


def test_forward_outcome_capture_is_fail_soft():
    def failing_runner(**kwargs):
        raise ConnectionError(
            "TWS unavailable"
        )

    result = (
        eod.run_forward_outcome_research_capture(
            runner=failing_runner,
            current_date="2026-08-18",
        )
    )

    assert result["success"] is False
    assert result["status"] == "ERROR"

    assert (
        result["as_of_date"]
        == "2026-08-18"
    )

    assert (
        "TWS unavailable"
        in result["message"]
    )


def test_automatic_eod_worker_enables_forward_outcomes(
    monkeypatch,
):
    captured = {}

    sentinel_runner = object()

    class OneCycleStop:
        def __init__(self):
            self.stopped = False

        def is_set(self):
            return self.stopped

        def wait(self, seconds):
            self.stopped = True
            return True

    current_datetime = datetime(
        2026,
        8,
        18,
        16,
        10,
        tzinfo=eod.TORONTO_TIMEZONE,
    )

    monkeypatch.setattr(
        eod,
        "normalize_current_datetime",
        lambda: current_datetime,
    )

    monkeypatch.setattr(
        eod,
        "load_last_run_date",
        lambda: None,
    )

    monkeypatch.setattr(
        eod,
        "get_recoverable_eod_datetime",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        eod,
        "run_candidate_forward_outcome_refresh",
        sentinel_runner,
    )

    def fake_cycle(**kwargs):
        captured.update(
            kwargs
        )

        return {
            "success": True,
            "status": "NOT_DUE",
        }

    monkeypatch.setattr(
        eod,
        "run_automatic_eod_cycle",
        fake_cycle,
    )

    eod.automatic_eod_worker(
        paper_engine=object(),
        stop_event=OneCycleStop(),
        check_seconds=1,
    )

    assert (
        captured[
            "forward_outcome_runner"
        ]
        is sentinel_runner
    )
