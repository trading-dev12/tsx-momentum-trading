import core.application_restart_alert as alert_module


def use_test_queue(
    monkeypatch,
    tmp_path,
):
    queue_file = (
        tmp_path
        / "pending_application_restart_alerts.json"
    )

    monkeypatch.setattr(
        alert_module,
        "PENDING_RESTART_ALERTS_FILE",
        queue_file,
    )

    monkeypatch.setattr(
        alert_module,
        "RUNTIME_FOLDER",
        tmp_path,
    )

    return queue_file


def test_normal_start_does_not_queue_alert(
    monkeypatch,
    tmp_path,
):
    use_test_queue(
        monkeypatch,
        tmp_path,
    )

    result = (
        alert_module
        .queue_application_restart_alert(
            {
                "transition": "STARTED",
                "previous_last_heartbeat": None,
                "downtime_seconds": None,
            }
        )
    )

    assert result is None

    assert (
        alert_module
        .load_pending_application_restart_alerts()
        == []
    )


def test_unexpected_restart_is_queued(
    monkeypatch,
    tmp_path,
):
    use_test_queue(
        monkeypatch,
        tmp_path,
    )

    transition = {
        "transition": "UNEXPECTED_RESTART",
        "previous_last_heartbeat": (
            "2026-08-07T10:00:00-04:00"
        ),
        "downtime_seconds": 900,
    }

    result = (
        alert_module
        .queue_application_restart_alert(
            transition
        )
    )

    alerts = (
        alert_module
        .load_pending_application_restart_alerts()
    )

    assert result is not None
    assert len(alerts) == 1

    assert (
        alerts[0]["transition"]
        == "UNEXPECTED_RESTART"
    )

    assert (
        alerts[0]["downtime_seconds"]
        == 900
    )


def test_failed_telegram_delivery_keeps_alert(
    monkeypatch,
    tmp_path,
):
    use_test_queue(
        monkeypatch,
        tmp_path,
    )

    alert_module.queue_application_restart_alert(
        {
            "transition": "UNEXPECTED_RESTART",
            "previous_last_heartbeat": (
                "2026-08-07T10:00:00-04:00"
            ),
            "downtime_seconds": 900,
        }
    )

    def failed_sender(message):
        return {
            "success": False,
            "message": "Internet unavailable.",
        }

    result = (
        alert_module
        .try_send_pending_application_restart_alert(
            sender=failed_sender,
        )
    )

    assert result["sent"] is False
    assert result["pending"] is True

    alerts = (
        alert_module
        .load_pending_application_restart_alerts()
    )

    assert len(alerts) == 1


def test_successful_delivery_removes_alert(
    monkeypatch,
    tmp_path,
):
    use_test_queue(
        monkeypatch,
        tmp_path,
    )

    alert_module.queue_application_restart_alert(
        {
            "transition": "UNEXPECTED_RESTART",
            "previous_last_heartbeat": (
                "2026-08-07T10:00:00-04:00"
            ),
            "downtime_seconds": 900,
        }
    )

    sent_messages = []

    def successful_sender(message):
        sent_messages.append(
            message
        )

        return {
            "success": True,
            "message": "Sent.",
        }

    result = (
        alert_module
        .try_send_pending_application_restart_alert(
            sender=successful_sender,
        )
    )

    assert result["sent"] is True
    assert result["pending"] is False

    assert len(sent_messages) == 1

    assert (
        "unexpected interruption"
        in sent_messages[0]
    )

    assert (
        "15m 0s"
        in sent_messages[0]
    )

    assert (
        alert_module
        .load_pending_application_restart_alerts()
        == []
    )