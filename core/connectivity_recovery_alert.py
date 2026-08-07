"""
Persistent internet recovery alert handling for Northstar.

Recovery notifications are stored locally before Telegram is
attempted so a temporary Telegram failure does not lose the alert.
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

PENDING_RECOVERY_FILE = (
    RUNTIME_FOLDER
    / "pending_connectivity_recovery.json"
)


def save_pending_recovery_alert(
    recovery_result,
):
    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    event = {
        "outage_started_at": recovery_result.get(
            "outage_started_at"
        ),
        "recovered_at": recovery_result.get(
            "recovered_at"
        ),
        "downtime_seconds": recovery_result.get(
            "downtime_seconds"
        ),
    }

    PENDING_RECOVERY_FILE.write_text(
        json.dumps(
            event,
            indent=2,
        ),
        encoding="utf-8",
    )

    return event


def load_pending_recovery_alert():
    if not PENDING_RECOVERY_FILE.exists():
        return None

    try:
        data = json.loads(
            PENDING_RECOVERY_FILE.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    if not isinstance(data, dict):
        return None

    return data


def clear_pending_recovery_alert():
    try:
        PENDING_RECOVERY_FILE.unlink(
            missing_ok=True,
        )

    except OSError:
        return False

    return True


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


def build_recovery_message(
    event,
):
    outage_started_at = event.get(
        "outage_started_at"
    ) or "Unknown"

    recovered_at = event.get(
        "recovered_at"
    ) or "Unknown"

    downtime = format_downtime(
        event.get(
            "downtime_seconds"
        )
    )

    return (
        "✅ Northstar internet connection restored.\n"
        f"Outage detected: {outage_started_at}\n"
        f"Restored: {recovered_at}\n"
        f"Downtime: {downtime}\n"
        "Automatic recovery monitoring is active."
    )


def try_send_pending_recovery_alert(
    sender=None,
):
    event = load_pending_recovery_alert()

    if event is None:
        return {
            "pending": False,
            "sent": False,
        }

    if sender is None:
        sender = send_telegram_message

    message = build_recovery_message(
        event
    )

    result = sender(
        message
    )

    if (
        isinstance(result, dict)
        and result.get("success") is True
    ):
        clear_pending_recovery_alert()

        return {
            "pending": False,
            "sent": True,
            "result": result,
        }

    return {
        "pending": True,
        "sent": False,
        "result": result,
    }