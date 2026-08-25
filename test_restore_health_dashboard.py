from datetime import datetime

import mobile_dashboard.backup_health as backup_health


def configure_common_backup_state(
    monkeypatch,
    restore_status,
    restore_schedule,
):
    monkeypatch.setattr(
        backup_health,
        "load_local_backup_settings",
        lambda: {
            "external_backup_root":
                r"D:\Northstar_Backups"
        },
    )

    monkeypatch.setattr(
        backup_health,
        "external_backup_available",
        lambda path: False,
    )

    monkeypatch.setattr(
        backup_health,
        "load_backup_status",
        lambda: {
            "last_backup_type":
                "LOCAL_FALLBACK",
            "last_backup_success":
                True,
            "last_external_success":
                "2026-08-25T09:19:00-04:00",
        },
    )

    monkeypatch.setattr(
        backup_health,
        "load_restore_test_status",
        lambda: restore_status,
    )

    monkeypatch.setattr(
        backup_health,
        "get_restore_test_schedule",
        lambda current_datetime=None:
            restore_schedule,
    )


def test_recent_restore_test_is_healthy(
    monkeypatch,
):
    configure_common_backup_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-25T09:35:00-04:00",
            "last_success":
                "2026-08-25T09:35:00-04:00",
            "last_test_success":
                True,
            "last_test_backup_path":
                r"D:\Northstar_Backups\2026-08-25",
        },
        {
            "due": False,
            "next_due":
                datetime(
                    2026,
                    9,
                    24,
                    9,
                    35,
                ),
            "seconds_until_due":
                29 * 86400,
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                26,
                9,
                35,
            )
        )
    )

    assert (
        data["restore_test_status"]
        == "PASS"
    )

    assert (
        data["restore_test_health"]
        == "PASS"
    )

    assert (
        "Sep 24, 2026"
        in data["next_restore_test"]
    )


def test_overdue_restore_test_warns(
    monkeypatch,
):
    configure_common_backup_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-01T09:35:00-04:00",
            "last_success":
                "2026-08-01T09:35:00-04:00",
            "last_test_success":
                True,
        },
        {
            "due": True,
            "next_due":
                datetime(
                    2026,
                    8,
                    31,
                    9,
                    35,
                ),
            "seconds_until_due":
                -86400,
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                9,
                1,
                9,
                35,
            )
        )
    )

    assert (
        data["restore_test_status"]
        == "DUE"
    )

    assert (
        data["restore_test_health"]
        == "WARNING"
    )

    assert (
        "OVERDUE BY"
        in data["restore_test_countdown"]
    )


def test_failed_restore_test_is_fail(
    monkeypatch,
):
    configure_common_backup_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-26T09:35:00-04:00",
            "last_success":
                "2026-08-25T09:35:00-04:00",
            "last_test_success":
                False,
        },
        {
            "due": False,
            "next_due":
                datetime(
                    2026,
                    9,
                    24,
                    9,
                    35,
                ),
            "seconds_until_due":
                29 * 86400,
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                26,
                10,
                0,
            )
        )
    )

    assert (
        data["restore_test_status"]
        == "FAIL"
    )

    assert (
        data["restore_test_health"]
        == "FAIL"
    )
