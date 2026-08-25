from datetime import datetime, timedelta

from core.market_hours import (
    TORONTO_TIMEZONE,
    get_latest_tsx_trading_day_on_or_before,
    get_next_tsx_trading_day,
    get_tsx_market_close_time,
    is_tsx_trading_day,
)
from utilities.backup_manager import (
    external_backup_available,
    load_backup_status,
    load_local_backup_settings,
    resolve_backup_root,
)
from utilities.restore_verifier import (
    get_restore_test_schedule,
    load_restore_test_status,
)


BACKUP_DELAY_MINUTES = 5
PHYSICAL_BACKUP_INTERVAL_DAYS = 7


def normalize_dashboard_datetime(
    current_datetime=None,
):
    if current_datetime is None:
        return datetime.now(
            TORONTO_TIMEZONE
        )

    if current_datetime.tzinfo is None:
        return current_datetime.replace(
            tzinfo=TORONTO_TIMEZONE
        )

    return current_datetime.astimezone(
        TORONTO_TIMEZONE
    )


def scheduled_backup_datetime(
    trading_date,
):
    close_time = (
        get_tsx_market_close_time(
            trading_date
        )
    )

    return (
        datetime.combine(
            trading_date,
            close_time,
            tzinfo=TORONTO_TIMEZONE,
        )
        + timedelta(
            minutes=BACKUP_DELAY_MINUTES
        )
    )


def get_backup_schedule(
    current_datetime=None,
):
    """
    Return the last backup that should already
    have occurred and the next scheduled EOD backup.
    """

    now = normalize_dashboard_datetime(
        current_datetime
    )

    today = now.date()

    if is_tsx_trading_day(today):
        today_backup = (
            scheduled_backup_datetime(
                today
            )
        )

        if now < today_backup:
            previous_date = (
                get_latest_tsx_trading_day_on_or_before(
                    today
                    - timedelta(days=1)
                )
            )

            last_required = (
                scheduled_backup_datetime(
                    previous_date
                )
            )

            next_expected = (
                today_backup
            )

        else:
            last_required = (
                today_backup
            )

            next_date = (
                get_next_tsx_trading_day(
                    today
                )
            )

            next_expected = (
                scheduled_backup_datetime(
                    next_date
                )
            )

    else:
        previous_date = (
            get_latest_tsx_trading_day_on_or_before(
                today
            )
        )

        last_required = (
            scheduled_backup_datetime(
                previous_date
            )
        )

        next_date = (
            get_next_tsx_trading_day(
                today
            )
        )

        next_expected = (
            scheduled_backup_datetime(
                next_date
            )
        )

    return {
        "now": now,
        "last_required": last_required,
        "next_expected": next_expected,
    }


def parse_backup_timestamp(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value)
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=TORONTO_TIMEZONE
        )
    else:
        parsed = parsed.astimezone(
            TORONTO_TIMEZONE
        )

    return parsed


def format_backup_timestamp(value):
    parsed = parse_backup_timestamp(
        value
    )

    if parsed is None:
        return "Never recorded"

    return parsed.strftime(
        "%b %d, %Y %I:%M %p"
    ).replace(
        " 0",
        " ",
    )


def format_duration(seconds):
    seconds = max(
        0,
        int(seconds),
    )

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes = remainder // 60

    parts = []

    if days:
        parts.append(
            f"{days}d"
        )

    if hours or days:
        parts.append(
            f"{hours}h"
        )

    parts.append(
        f"{minutes}m"
    )

    return " ".join(parts)


def get_physical_backup_schedule(
    last_external_success,
    current_datetime=None,
):
    """
    Physical SanDisk backups are required once
    every seven days from the last successful
    external backup.
    """

    now = normalize_dashboard_datetime(
        current_datetime
    )

    last_external = parse_backup_timestamp(
        last_external_success
    )

    if last_external is None:
        return {
            "now": now,
            "last_external": None,
            "next_due": now,
            "due": True,
            "seconds_until_due": 0,
        }

    next_due = (
        last_external
        + timedelta(
            days=PHYSICAL_BACKUP_INTERVAL_DAYS
        )
    )

    seconds_until_due = (
        next_due - now
    ).total_seconds()

    return {
        "now": now,
        "last_external": last_external,
        "next_due": next_due,
        "due": seconds_until_due <= 0,
        "seconds_until_due": (
            seconds_until_due
        ),
    }


def build_backup_health_data(
    current_datetime=None,
):
    now = normalize_dashboard_datetime(
        current_datetime
    )

    status = load_backup_status()

    restore_status_data = (
        load_restore_test_status()
    )

    restore_schedule = (
        get_restore_test_schedule(
            now
        )
    )

    local_settings = (
        load_local_backup_settings()
    )

    external_value = (
        local_settings.get(
            "external_backup_root"
        )
    )

    external_root = None
    external_connected = False

    if external_value:
        external_root = (
            resolve_backup_root(
                external_value
            )
        )

        external_connected = (
            external_backup_available(
                external_root
            )
        )

    physical_schedule = (
        get_physical_backup_schedule(
            status.get(
                "last_external_success"
            ),
            now,
        )
    )

    last_external = (
        physical_schedule[
            "last_external"
        ]
    )

    physical_due = (
        physical_schedule["due"]
    )

    external_current = (
        last_external is not None
        and not physical_due
    )

    if last_external is None:
        backup_age = (
            "No tracked physical backup"
        )
    else:
        backup_age = format_duration(
            (
                now - last_external
            ).total_seconds()
        )

    if not external_value:
        drive_status = "NOT CONFIGURED"
        drive_health = "FAIL"

    elif physical_due:
        if external_connected:
            drive_status = (
                "CONNECTED - BACKUP DUE"
            )
        else:
            drive_status = (
                "DISCONNECTED - BACKUP DUE"
            )

        drive_health = "WARNING"

    elif external_connected:
        drive_status = "CONNECTED"
        drive_health = "PASS"

    else:
        drive_status = "DISCONNECTED - OK"
        drive_health = "PASS"

    if physical_due:
        countdown = "DUE NOW"

        if last_external is None:
            reminder = (
                "Connect SanDisk - "
                "physical backup needed"
            )
        else:
            overdue_seconds = abs(
                physical_schedule[
                    "seconds_until_due"
                ]
            )

            reminder = (
                "Physical backup overdue by "
                f"{format_duration(overdue_seconds)}"
            )

        reminder_health = "WARNING"

    else:
        countdown = format_duration(
            physical_schedule[
                "seconds_until_due"
            ]
        )

        reminder = (
            "Physical backup due in "
            f"{countdown}"
        )

        reminder_health = "PASS"

    last_backup_type = status.get(
        "last_backup_type",
        "UNKNOWN",
    )

    last_backup_success = status.get(
        "last_backup_success",
        True,
    )

    if not last_backup_success:
        fallback_text = (
            "LAST DAILY BACKUP FAILED"
        )
        fallback_health = "FAIL"

    elif last_backup_type in (
        "LOCAL",
        "LOCAL_FALLBACK",
    ):
        fallback_text = (
            "DAILY LOCAL BACKUP OK"
        )
        fallback_health = "PASS"

    else:
        fallback_text = (
            "LOCAL BACKUP READY"
        )
        fallback_health = "PASS"

    restore_last_success = (
        restore_status_data.get(
            "last_success"
        )
    )

    restore_last_attempt = (
        restore_status_data.get(
            "last_attempt"
        )
    )

    restore_last_test_success = (
        restore_status_data.get(
            "last_test_success"
        )
    )

    restore_due = bool(
        restore_schedule.get(
            "due",
            True,
        )
    )

    restore_seconds = (
        restore_schedule.get(
            "seconds_until_due",
            0,
        )
    )

    try:
        restore_seconds = float(
            restore_seconds
        )
    except (
        TypeError,
        ValueError,
    ):
        restore_seconds = 0

    if restore_last_success is None:
        restore_test_status = "DUE"
        restore_test_health = "WARNING"

    elif restore_last_test_success is False:
        restore_test_status = "FAIL"
        restore_test_health = "FAIL"

    elif restore_due:
        restore_test_status = "DUE"
        restore_test_health = "WARNING"

    else:
        restore_test_status = "PASS"
        restore_test_health = "PASS"

    if restore_due:
        if restore_seconds < 0:
            restore_test_countdown = (
                "OVERDUE BY "
                + format_duration(
                    abs(
                        restore_seconds
                    )
                )
            )
        else:
            restore_test_countdown = (
                "DUE NOW"
            )

    else:
        restore_test_countdown = (
            format_duration(
                restore_seconds
            )
        )

    restore_next_due = (
        restore_schedule.get(
            "next_due"
        )
    )

    if isinstance(
        restore_next_due,
        datetime,
    ):
        restore_next_due_text = (
            restore_next_due
            .astimezone(
                TORONTO_TIMEZONE
            )
            .strftime(
                "%b %d, %Y %I:%M %p"
            )
            .replace(
                " 0",
                " ",
            )
        )
    else:
        restore_next_due_text = (
            "Unknown"
        )

    return {
        "drive_status": drive_status,
        "drive_health": drive_health,
        "external_connected": (
            external_connected
        ),
        "external_root": (
            str(external_root)
            if external_root
            else "--"
        ),
        "last_external": (
            format_backup_timestamp(
                status.get(
                    "last_external_success"
                )
            )
        ),
        "backup_age": backup_age,
        "external_current": (
            external_current
        ),
        "next_expected": (
            physical_schedule[
                "next_due"
            ].strftime(
                "%b %d, %Y %I:%M %p"
            ).replace(
                " 0",
                " ",
            )
        ),
        "countdown": countdown,
        "reminder": reminder,
        "reminder_health": (
            reminder_health
        ),
        "last_backup_type": (
            last_backup_type
        ),
        "last_backup_path": (
            status.get(
                "last_backup_path",
                "--",
            )
        ),
        "local_fallback": (
            fallback_text
        ),
        "local_fallback_health": (
            fallback_health
        ),
        "restore_test_status": (
            restore_test_status
        ),
        "restore_test_health": (
            restore_test_health
        ),
        "last_restore_test": (
            format_backup_timestamp(
                restore_last_attempt
            )
        ),
        "last_successful_restore_test": (
            format_backup_timestamp(
                restore_last_success
            )
        ),
        "next_restore_test": (
            restore_next_due_text
        ),
        "restore_test_countdown": (
            restore_test_countdown
        ),
        "restore_test_backup_path": (
            restore_status_data.get(
                "last_test_backup_path",
                "--",
            )
        ),
    }
