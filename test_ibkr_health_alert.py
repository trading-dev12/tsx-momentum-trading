import core.ibkr_health_alert as ibkr_alert


def configure_temp_alert_file(
    monkeypatch,
    tmp_path,
):
    alert_file = (
        tmp_path
        / "pending_ibkr_health_alerts.json"
    )

    monkeypatch.setattr(
        ibkr_alert,
        "PENDING_IBKR_ALERTS_FILE",
        alert_file,
    )

    return alert_file


def test_failed_telegram_keeps_tws_down_alert(
    monkeypatch,
    tmp_path,
):
    alert_file = configure_temp_alert_file(
        monkeypatch,
        tmp_path,
    )

    down_event = {
        "transition": "TWS_DOWN",
        "unavailable_started_at": (
            "2026-08-07T14:00:00-04:00"
        ),
        "recovered_at": None,
        "downtime_seconds": None,
    }

    ibkr_alert.queue_ibkr_health_alert(
        down_event
    )

    sent_messages = []

    def failed_sender(message):
        sent_messages.append(message)

        return {
            "success": False,
            "error": "Temporary Telegram failure",
        }

    result = (
        ibkr_alert
        .try_send_pending_ibkr_alert(
            sender=failed_sender,
        )
    )

    assert result["sent"] is False
    assert result["pending"] is True
    assert alert_file.exists()

    pending = (
        ibkr_alert
        .load_pending_ibkr_alerts()
    )

    assert len(pending) == 1
    assert (
        pending[0]["transition"]
        == "TWS_DOWN"
    )

    assert len(sent_messages) == 1
    assert (
        "IBKR/TWS unavailable"
        in sent_messages[0]
    )


def test_down_and_recovery_remain_in_order(
    monkeypatch,
    tmp_path,
):
    configure_temp_alert_file(
        monkeypatch,
        tmp_path,
    )

    down_event = {
        "transition": "TWS_DOWN",
        "unavailable_started_at": (
            "2026-08-07T14:00:00-04:00"
        ),
        "recovered_at": None,
        "downtime_seconds": None,
    }

    recovery_event = {
        "transition": "TWS_RECOVERED",
        "unavailable_started_at": (
            "2026-08-07T14:00:00-04:00"
        ),
        "recovered_at": (
            "2026-08-07T14:07:15-04:00"
        ),
        "downtime_seconds": 435,
    }

    ibkr_alert.queue_ibkr_health_alert(
        down_event
    )

    ibkr_alert.queue_ibkr_health_alert(
        recovery_event
    )

    pending = (
        ibkr_alert
        .load_pending_ibkr_alerts()
    )

    assert [
        event["transition"]
        for event in pending
    ] == [
        "TWS_DOWN",
        "TWS_RECOVERED",
    ]


def test_successful_sends_preserve_queue_order(
    monkeypatch,
    tmp_path,
):
    alert_file = configure_temp_alert_file(
        monkeypatch,
        tmp_path,
    )

    ibkr_alert.queue_ibkr_health_alert(
        {
            "transition": "TWS_DOWN",
            "unavailable_started_at": (
                "2026-08-07T14:00:00-04:00"
            ),
            "recovered_at": None,
            "downtime_seconds": None,
        }
    )

    ibkr_alert.queue_ibkr_health_alert(
        {
            "transition": "TWS_RECOVERED",
            "unavailable_started_at": (
                "2026-08-07T14:00:00-04:00"
            ),
            "recovered_at": (
                "2026-08-07T14:07:15-04:00"
            ),
            "downtime_seconds": 435,
        }
    )

    sent_messages = []

    def successful_sender(message):
        sent_messages.append(message)

        return {
            "success": True,
        }

    first_result = (
        ibkr_alert
        .try_send_pending_ibkr_alert(
            sender=successful_sender,
        )
    )

    assert first_result["sent"] is True
    assert first_result["pending"] is True

    remaining = (
        ibkr_alert
        .load_pending_ibkr_alerts()
    )

    assert len(remaining) == 1
    assert (
        remaining[0]["transition"]
        == "TWS_RECOVERED"
    )

    second_result = (
        ibkr_alert
        .try_send_pending_ibkr_alert(
            sender=successful_sender,
        )
    )

    assert second_result["sent"] is True
    assert second_result["pending"] is False
    assert not alert_file.exists()

    assert len(sent_messages) == 2

    assert (
        "IBKR/TWS unavailable"
        in sent_messages[0]
    )

    assert (
        "IBKR/TWS restored"
        in sent_messages[1]
    )

    assert "7m 15s" in sent_messages[1]