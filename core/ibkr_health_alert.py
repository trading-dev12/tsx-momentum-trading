"""
Persistent IBKR/TWS health alert queue for Northstar.

Health alerts are stored locally before Telegram delivery is
attempted so temporary Telegram failures do not lose events.
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

PENDING_IBKR_ALERTS_FILE = (
    RUNTIME_FOLDER
    / "pending_ibkr_health_alerts.json"
)


def load_pending_ibkr_alerts():
    if not PENDING_IBKR_ALERTS_FILE.exists():
        return []

    try:
        data = json.loads(
            PENDING_IBKR_ALERTS_FILE.read_text(
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


def save_pending_ibkr_alerts(
    alerts,
):
    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not alerts:
        try:
            PENDING_IBKR_ALERTS_FILE.unlink(
                missing_ok=True,
            )

        except OSError:
            pass

        return

    PENDING_IBKR_ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            indent=2,
        ),
        encoding="utf-8",
    )


def queue_ibkr_health_alert(
    transition_result,
):
    transition = transition_result.get(
        "transition"
    )

    if transition not in (
        "TWS_DOWN",
        "TWS_RECOVERED",
    ):
        return None

    event = {
        "transition": transition,
        "unavailable_started_at": (
            transition_result.get(
                "unavailable_started_at"
            )
        ),
        "recovered_at": (
            transition_result.get(
                "recovered_at"
            )
        ),
        "downtime_seconds": (
            transition_result.get(
                "downtime_seconds"
            )
        ),
    }

    alerts = load_pending_ibkr_alerts()

    if event not in alerts:
        alerts.append(
            event
        )

        save_pending_ibkr_alerts(
            alerts
        )

    return event


def format_downtime(
    downtime_seconds,
):
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


def build_ibkr_health_message(
    event,
):
    transition = event.get(
        "transition"
    )

    unavailable_started_at = (
        event.get(
            "unavailable_started_at"
        )
        or "Unknown"
    )

    if transition == "TWS_DOWN":
        return (
            "⚠️ Northstar IBKR/TWS unavailable.\n"
            f"Detected: {unavailable_started_at}\n"
            "IBKR market data is temporarily unavailable.\n"
            "Automatic reconnect monitoring is active."
        )

    if transition == "TWS_RECOVERED":
        recovered_at = (
            event.get(
                "recovered_at"
            )
            or "Unknown"
        )

        downtime = format_downtime(
            event.get(
                "downtime_seconds"
            )
        )

        return (
            "✅ Northstar IBKR/TWS restored.\n"
            f"Unavailable since: {unavailable_started_at}\n"
            f"Restored: {recovered_at}\n"
            f"Downtime: {downtime}\n"
            "Automatic IBKR data recovery is active."
        )

    raise ValueError(
        "Unsupported IBKR health transition."
    )


def try_send_pending_ibkr_alert(
    sender=None,
):
    alerts = load_pending_ibkr_alerts()

    if not alerts:
        return {
            "pending": False,
            "sent": False,
        }

    if sender is None:
        sender = send_telegram_message

    event = alerts[0]

    message = build_ibkr_health_message(
        event
    )

    result = sender(
        message
    )

    if (
        isinstance(result, dict)
        and result.get("success") is True
    ):
        alerts.pop(0)

        save_pending_ibkr_alerts(
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