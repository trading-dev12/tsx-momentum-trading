from datetime import datetime as RealDateTime

import gui.trading_workstation as workstation_module


class ImmediateThread:
    def __init__(
        self,
        target,
        daemon=None,
    ):
        self.target = target
        self.daemon = daemon

    def start(self):
        self.target()


class TradingWindowDateTime(RealDateTime):
    @classmethod
    def now(cls):
        return RealDateTime(
            2026,
            8,
            7,
            10,
            0,
            0,
        )


class AfterHoursDateTime(RealDateTime):
    @classmethod
    def now(cls):
        return RealDateTime(
            2026,
            8,
            7,
            18,
            0,
            0,
        )


def build_workstation(
    internet_online=True,
):
    workstation = (
        workstation_module
        .TradingWorkstation
        .__new__(
            workstation_module.TradingWorkstation
        )
    )

    workstation.internet_connectivity_result = {
        "online": internet_online,
    }

    workstation.ibkr_health_check_in_flight = False
    workstation.last_ibkr_health_check_started = None

    return workstation


def test_ibkr_check_skipped_when_internet_offline(
    monkeypatch,
):
    workstation = build_workstation(
        internet_online=False,
    )

    def unexpected_check():
        raise AssertionError(
            "TWS health must not be checked "
            "during an internet outage."
        )

    monkeypatch.setattr(
        workstation_module,
        "check_ibkr_tws_available",
        unexpected_check,
    )

    workstation.start_ibkr_health_check_if_due()

    assert (
        workstation.ibkr_health_check_in_flight
        is False
    )


def test_ibkr_check_skipped_after_monitoring_window(
    monkeypatch,
):
    workstation = build_workstation()

    monkeypatch.setattr(
        workstation_module,
        "datetime",
        AfterHoursDateTime,
    )

    monkeypatch.setattr(
        workstation_module,
        "is_tsx_trading_day",
        lambda date: True,
    )

    def unexpected_check():
        raise AssertionError(
            "TWS health must not be checked "
            "after the monitoring window."
        )

    monkeypatch.setattr(
        workstation_module,
        "check_ibkr_tws_available",
        unexpected_check,
    )

    workstation.start_ibkr_health_check_if_due()

    assert (
        workstation.ibkr_health_check_in_flight
        is False
    )


def test_tws_down_is_queued_and_sent(
    monkeypatch,
):
    workstation = build_workstation()

    monkeypatch.setattr(
        workstation_module,
        "datetime",
        TradingWindowDateTime,
    )

    monkeypatch.setattr(
        workstation_module,
        "is_tsx_trading_day",
        lambda date: True,
    )

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    monkeypatch.setattr(
        workstation_module,
        "check_ibkr_tws_available",
        lambda: {
            "available": False,
            "host": "127.0.0.1",
            "port": 7496,
            "error": "Connection refused",
        },
    )

    transition = {
        "transition": "TWS_DOWN",
        "status": "UNAVAILABLE",
        "unavailable_started_at": (
            "2026-08-07T10:00:00-04:00"
        ),
        "recovered_at": None,
        "downtime_seconds": None,
    }

    monkeypatch.setattr(
        workstation_module,
        "record_ibkr_tws_status",
        lambda available: transition,
    )

    queued = []

    def fake_queue(event):
        queued.append(event)
        return event

    monkeypatch.setattr(
        workstation_module,
        "queue_ibkr_health_alert",
        fake_queue,
    )

    send_attempts = []

    def fake_send():
        send_attempts.append(True)

        return {
            "pending": False,
            "sent": True,
        }

    monkeypatch.setattr(
        workstation_module,
        "try_send_pending_ibkr_alert",
        fake_send,
    )

    workstation.start_ibkr_health_check_if_due()

    assert (
        workstation.ibkr_health_result[
            "available"
        ]
        is False
    )

    assert queued == [transition]
    assert send_attempts == [True]

    assert (
        workstation.ibkr_health_transition[
            "transition"
        ]
        == "TWS_DOWN"
    )

    assert (
        workstation.ibkr_health_check_in_flight
        is False
    )


def test_tws_recovery_is_queued_and_sent(
    monkeypatch,
):
    workstation = build_workstation()

    monkeypatch.setattr(
        workstation_module,
        "datetime",
        TradingWindowDateTime,
    )

    monkeypatch.setattr(
        workstation_module,
        "is_tsx_trading_day",
        lambda date: True,
    )

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    monkeypatch.setattr(
        workstation_module,
        "check_ibkr_tws_available",
        lambda: {
            "available": True,
            "host": "127.0.0.1",
            "port": 7496,
            "error": None,
        },
    )

    transition = {
        "transition": "TWS_RECOVERED",
        "status": "AVAILABLE",
        "unavailable_started_at": (
            "2026-08-07T09:50:00-04:00"
        ),
        "recovered_at": (
            "2026-08-07T10:00:00-04:00"
        ),
        "downtime_seconds": 600,
    }

    monkeypatch.setattr(
        workstation_module,
        "record_ibkr_tws_status",
        lambda available: transition,
    )

    queued = []

    def fake_queue(event):
        queued.append(event)
        return event

    monkeypatch.setattr(
        workstation_module,
        "queue_ibkr_health_alert",
        fake_queue,
    )

    send_attempts = []

    def fake_send():
        send_attempts.append(True)

        return {
            "pending": False,
            "sent": True,
        }

    monkeypatch.setattr(
        workstation_module,
        "try_send_pending_ibkr_alert",
        fake_send,
    )

    workstation.start_ibkr_health_check_if_due()

    assert (
        workstation.ibkr_health_result[
            "available"
        ]
        is True
    )

    assert queued == [transition]
    assert send_attempts == [True]

    assert (
        workstation.ibkr_health_transition[
            "transition"
        ]
        == "TWS_RECOVERED"
    )

    assert (
        workstation.ibkr_health_check_in_flight
        is False
    )