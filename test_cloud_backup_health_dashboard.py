from datetime import datetime

import mobile_dashboard.backup_health as backup_health


def configure_common_state(
    monkeypatch,
    cloud_status,
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
        "load_cloud_backup_status",
        lambda: cloud_status,
    )

    monkeypatch.setattr(
        backup_health,
        "load_restore_test_status",
        lambda: {
            "last_attempt":
                "2026-08-25T09:35:00-04:00",
            "last_success":
                "2026-08-25T09:35:00-04:00",
            "last_test_success":
                True,
        },
    )

    monkeypatch.setattr(
        backup_health,
        "get_restore_test_schedule",
        lambda current_datetime=None: {
            "due": False,
            "next_due": datetime(
                2026,
                9,
                24,
                9,
                35,
            ),
            "seconds_until_due":
                30 * 86400,
        },
    )


def test_recent_cloud_backup_is_pass(
    monkeypatch,
):
    configure_common_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-25T09:56:00-04:00",
            "last_success":
                "2026-08-25T09:56:00-04:00",
            "last_backup_success":
                True,
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                25,
                10,
                0,
            )
        )
    )

    assert (
        data["cloud_backup_status"]
        == "PASS"
    )

    assert (
        data["cloud_backup_health"]
        == "PASS"
    )

    assert (
        "Aug 25, 2026 4:05 PM"
        in data["next_cloud_backup"]
    )


def test_cloud_backup_becomes_due_after_eod(
    monkeypatch,
):
    configure_common_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-24T16:06:00-04:00",
            "last_success":
                "2026-08-24T16:06:00-04:00",
            "last_backup_success":
                True,
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                25,
                17,
                0,
            )
        )
    )

    assert (
        data["cloud_backup_status"]
        == "DUE"
    )

    assert (
        data["cloud_backup_health"]
        == "WARNING"
    )


def test_latest_cloud_failure_is_fail(
    monkeypatch,
):
    configure_common_state(
        monkeypatch,
        {
            "last_attempt":
                "2026-08-25T16:06:00-04:00",
            "last_success":
                "2026-08-24T16:06:00-04:00",
            "last_backup_success":
                False,
            "errors": [
                "simulated OneDrive failure"
            ],
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                25,
                17,
                0,
            )
        )
    )

    assert (
        data["cloud_backup_status"]
        == "FAIL"
    )

    assert (
        data["cloud_backup_health"]
        == "FAIL"
    )
