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


BACKUP_DELAY_MINUTES = 5


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


def build_backup_health_data(
    current_datetime=None,
):
    now = normalize_dashboard_datetime(
        current_datetime
    )

    schedule = get_backup_schedule(
        now
    )

    status = load_backup_status()
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

    last_external = (
        parse_backup_timestamp(
            status.get(
                "last_external_success"
            )
        )
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

    external_current = bool(
        last_external is not None
        and last_external
        >= schedule["last_required"]
    )

    if not external_value:
        drive_status = "NOT CONFIGURED"
        drive_health = "FAIL"

    elif not external_connected:
        drive_status = "DISCONNECTED"
        drive_health = "WARNING"

    elif last_external is None:
        drive_status = "CONNECTED - BACKUP NEEDED"
        drive_health = "WARNING"

    elif not external_current:
        drive_status = "CONNECTED - BACKUP OVERDUE"
        drive_health = "WARNING"

    else:
        drive_status = "CONNECTED"
        drive_health = "PASS"

    countdown_seconds = (
        schedule["next_expected"]
        - now
    ).total_seconds()

    countdown = format_duration(
        countdown_seconds
    )

    if (
        last_external is not None
        and not external_current
    ):
        reminder = (
            "PHYSICAL BACKUP OVERDUE"
        )
        reminder_health = "WARNING"

    elif not external_connected:
        reminder = (
            f"Connect SanDisk - next EOD "
            f"backup in {countdown}"
        )
        reminder_health = "WARNING"

    else:
        reminder = (
            f"Next EOD backup in "
            f"{countdown}"
        )
        reminder_health = "PASS"

    last_backup_type = status.get(
        "last_backup_type",
        "UNKNOWN",
    )

    if (
        last_backup_type
        == "LOCAL_FALLBACK"
    ):
        fallback_text = "USED LAST BACKUP"
        fallback_health = "WARNING"
    else:
        fallback_text = "READY"
        fallback_health = "PASS"

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
            schedule[
                "next_expected"
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
    }
