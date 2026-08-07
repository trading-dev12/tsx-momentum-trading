import core.connectivity_recovery_alert as recovery_alert


def test_failed_telegram_keeps_pending_alert(
    monkeypatch,
    tmp_path,
):
    pending_file = (
        tmp_path
        / "pending_connectivity_recovery.json"
    )

    monkeypatch.setattr(
        recovery_alert,
        "PENDING_RECOVERY_FILE",
        pending_file,
    )

    recovery_alert.save_pending_recovery_alert(
        {
            "outage_started_at": (
                "2026-08-07T14:00:00-04:00"
            ),
            "recovered_at": (
                "2026-08-07T14:12:30-04:00"
            ),
            "downtime_seconds": 750,
        }
    )

    sent_messages = []

    def failed_sender(message):
        sent_messages.append(message)

        return {
            "success": False,
            "error": "Temporary Telegram failure",
        }

    result = (
        recovery_alert
        .try_send_pending_recovery_alert(
            sender=failed_sender,
        )
    )

    assert result["sent"] is False
    assert result["pending"] is True
    assert pending_file.exists()

    assert len(sent_messages) == 1
    assert "12m 30s" in sent_messages[0]
    assert (
        "internet connection restored"
        in sent_messages[0]
    )


def test_successful_retry_clears_pending_alert(
    monkeypatch,
    tmp_path,
):
    pending_file = (
        tmp_path
        / "pending_connectivity_recovery.json"
    )

    monkeypatch.setattr(
        recovery_alert,
        "PENDING_RECOVERY_FILE",
        pending_file,
    )

    recovery_alert.save_pending_recovery_alert(
        {
            "outage_started_at": (
                "2026-08-07T14:00:00-04:00"
            ),
            "recovered_at": (
                "2026-08-07T14:12:30-04:00"
            ),
            "downtime_seconds": 750,
        }
    )

    def failed_sender(message):
        return {
            "success": False,
        }

    first_result = (
        recovery_alert
        .try_send_pending_recovery_alert(
            sender=failed_sender,
        )
    )

    assert first_result["pending"] is True
    assert pending_file.exists()

    def successful_sender(message):
        return {
            "success": True,
        }

    second_result = (
        recovery_alert
        .try_send_pending_recovery_alert(
            sender=successful_sender,
        )
    )

    assert second_result["sent"] is True
    assert second_result["pending"] is False
    assert not pending_file.exists()