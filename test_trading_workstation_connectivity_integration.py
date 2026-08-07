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


def build_workstation():
    workstation = (
        workstation_module
        .TradingWorkstation
        .__new__(
            workstation_module.TradingWorkstation
        )
    )

    workstation.connectivity_check_in_flight = False
    workstation.last_connectivity_check_started = None

    return workstation


def test_offline_transition_is_recorded_without_telegram(
    monkeypatch,
):
    workstation = build_workstation()

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    monkeypatch.setattr(
        workstation_module,
        "check_internet_connectivity",
        lambda: {
            "online": False,
            "reachable_target": None,
            "failures": [],
        },
    )

    recorded_statuses = []

    def fake_record_connectivity_status(
        online,
    ):
        recorded_statuses.append(online)

        return {
            "transition": "OUTAGE_STARTED",
            "status": "OFFLINE",
            "outage_started_at": (
                "2026-08-07T14:00:00-04:00"
            ),
            "recovered_at": None,
            "downtime_seconds": None,
        }

    monkeypatch.setattr(
        workstation_module,
        "record_connectivity_status",
        fake_record_connectivity_status,
    )

    def unexpected_save(*args, **kwargs):
        raise AssertionError(
            "Recovery alert should not be saved "
            "while internet is offline."
        )

    monkeypatch.setattr(
        workstation_module,
        "save_pending_recovery_alert",
        unexpected_save,
    )

    def unexpected_send(*args, **kwargs):
        raise AssertionError(
            "Telegram should not be attempted "
            "while internet is offline."
        )

    monkeypatch.setattr(
        workstation_module,
        "try_send_pending_recovery_alert",
        unexpected_send,
    )

    workstation.start_connectivity_check_if_due()

    assert recorded_statuses == [False]

    assert (
        workstation.internet_connectivity_result[
            "online"
        ]
        is False
    )

    assert (
        workstation
        .internet_connectivity_transition[
            "transition"
        ]
        == "OUTAGE_STARTED"
    )

    assert (
        workstation.connectivity_check_in_flight
        is False
    )


def test_recovery_saves_and_attempts_telegram(
    monkeypatch,
):
    workstation = build_workstation()

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    monkeypatch.setattr(
        workstation_module,
        "check_internet_connectivity",
        lambda: {
            "online": True,
            "reachable_target": "Cloudflare",
            "failures": [],
        },
    )

    recovery_transition = {
        "transition": "RECOVERED",
        "status": "ONLINE",
        "outage_started_at": (
            "2026-08-07T14:00:00-04:00"
        ),
        "recovered_at": (
            "2026-08-07T14:12:30-04:00"
        ),
        "downtime_seconds": 750,
    }

    monkeypatch.setattr(
        workstation_module,
        "record_connectivity_status",
        lambda online: recovery_transition,
    )

    saved_alerts = []

    def fake_save_pending_recovery_alert(
        transition,
    ):
        saved_alerts.append(transition)

        return transition

    monkeypatch.setattr(
        workstation_module,
        "save_pending_recovery_alert",
        fake_save_pending_recovery_alert,
    )

    send_attempts = []

    def fake_try_send_pending_recovery_alert():
        send_attempts.append(True)

        return {
            "pending": False,
            "sent": True,
        }

    monkeypatch.setattr(
        workstation_module,
        "try_send_pending_recovery_alert",
        fake_try_send_pending_recovery_alert,
    )

    workstation.start_connectivity_check_if_due()

    assert saved_alerts == [
        recovery_transition
    ]

    assert send_attempts == [True]

    assert (
        workstation.internet_connectivity_result[
            "online"
        ]
        is True
    )

    assert (
        workstation
        .internet_connectivity_transition[
            "transition"
        ]
        == "RECOVERED"
    )

    assert (
        workstation
        .connectivity_recovery_alert_result[
            "sent"
        ]
        is True
    )

    assert (
        workstation.connectivity_check_in_flight
        is False
    )