"""
Persistent unexpected Northstar restart alert queue.

Restart alerts are stored locally before Telegram delivery is
attempted so an internet or Telegram failure does not lose the
notification.
"""

import json
from pathlib import Path

from notifications.telegram_notifier import (
    send_telegram_message,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

PENDING_RESTART_ALERTS_FILE = (
    RUNTIME_FOLDER
    / "pending_application_restart_alerts.json"
)


def load_pending_application_restart_alerts():
    """
    Load queued unexpected-restart alerts.
    """

    if not PENDING_RESTART_ALERTS_FILE.exists():
        return []

    try:
        data = json.loads(
            PENDING_RESTART_ALERTS_FILE.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []

    if not isinstance(data, list):
        return []

    return [
        event
        for event in data
        if isinstance(event, dict)
    ]


def save_pending_application_restart_alerts(
    alerts,
):
    """
    Persist queued unexpected-restart alerts.
    """

    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not alerts:
        try:
            PENDING_RESTART_ALERTS_FILE.unlink(
                missing_ok=True,
            )

        except OSError:
            pass

        return

    PENDING_RESTART_ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            indent=2,
        ),
        encoding="utf-8",
    )


def queue_application_restart_alert(
    transition_result,
):
    """
    Queue one unexpected-restart event.

    Normal STARTED transitions do not create alerts.
    """

    if transition_result.get(
        "transition"
    ) != "UNEXPECTED_RESTART":
        return None

    event = {
        "transition": "UNEXPECTED_RESTART",
        "previous_last_heartbeat": (
            transition_result.get(
                "previous_last_heartbeat"
            )
        ),
        "downtime_seconds": (
            transition_result.get(
                "downtime_seconds"
            )
        ),
    }

    alerts = (
        load_pending_application_restart_alerts()
    )

    if event not in alerts:
        alerts.append(
            event
        )

        save_pending_application_restart_alerts(
            alerts
        )

    return event


def format_downtime(
    downtime_seconds,
):
    """
    Format downtime for Telegram.
    """

    if downtime_seconds is None:
        return "Unknown"

    downtime_seconds = max(
        0,
        int(downtime_seconds),
    )

    hours, remainder = divmod(
        downtime_seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours:
        return (
            f"{hours}h "
            f"{minutes}m "
            f"{seconds}s"
        )

    if minutes:
        return (
            f"{minutes}m "
            f"{seconds}s"
        )

    return f"{seconds}s"


def build_application_restart_message(
    event,
):
    """
    Build the unexpected-restart Telegram message.
    """

    previous_heartbeat = (
        event.get(
            "previous_last_heartbeat"
        )
        or "Unknown"
    )

    downtime = format_downtime(
        event.get(
            "downtime_seconds"
        )
    )

    return (
        "⚠️ Northstar restarted after an unexpected interruption.\n"
        f"Last recorded heartbeat: {previous_heartbeat}\n"
        f"Approximate unavailable time: {downtime}\n"
        "Northstar is running again.\n"
        "The cause may have been a power interruption, Windows "
        "restart, application crash, or forced shutdown."
    )


def try_send_pending_application_restart_alert(
    sender=None,
):
    """
    Attempt delivery of the oldest queued restart alert.
    """

    alerts = (
        load_pending_application_restart_alerts()
    )

    if not alerts:
        return {
            "pending": False,
            "sent": False,
        }

    if sender is None:
        sender = send_telegram_message

    event = alerts[0]

    message = (
        build_application_restart_message(
            event
        )
    )

    result = sender(
        message
    )

    if (
        isinstance(result, dict)
        and result.get("success") is True
    ):
        alerts.pop(0)

        save_pending_application_restart_alerts(
            alerts
        )

        return {
            "pending": bool(alerts),
            "sent": True,
            "event": event,
            "result": result,
        }

    return {
        "pending": True,
        "sent": False,
        "event": event,
        "result": result,
    }