from datetime import datetime

import mobile_dashboard.backup_health as backup_health


def test_weekday_before_eod_counts_down_to_today():
    data = backup_health.get_backup_schedule(
        datetime(
            2026,
            8,
            25,
            9,
            30,
        )
    )

    assert (
        data["next_expected"].date().isoformat()
        == "2026-08-25"
    )

    assert (
        data["next_expected"].hour
        == 16
    )

    assert (
        data["next_expected"].minute
        == 5
    )


def test_weekday_after_eod_uses_next_trading_day():
    data = backup_health.get_backup_schedule(
        datetime(
            2026,
            8,
            25,
            17,
            0,
        )
    )

    assert (
        data["last_required"].date().isoformat()
        == "2026-08-25"
    )

    assert (
        data["next_expected"].date().isoformat()
        == "2026-08-26"
    )


def test_weekend_uses_previous_and_next_trading_days():
    data = backup_health.get_backup_schedule(
        datetime(
            2026,
            8,
            29,
            10,
            0,
        )
    )

    assert (
        data["last_required"].date().isoformat()
        == "2026-08-28"
    )

    assert (
        data["next_expected"].date().isoformat()
        == "2026-08-31"
    )


def test_disconnected_external_drive_warns(
    monkeypatch,
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
            "last_backup_path":
                r"C:\Northstar_Backups\2026-08-25",
            "last_external_success":
                "2026-08-24T16:10:00-04:00",
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                25,
                9,
                30,
            )
        )
    )

    assert (
        data["drive_status"]
        == "DISCONNECTED"
    )

    assert (
        data["drive_health"]
        == "WARNING"
    )

    assert (
        data["local_fallback"]
        == "USED LAST BACKUP"
    )


def test_current_external_backup_is_healthy(
    monkeypatch,
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
        lambda path: True,
    )

    monkeypatch.setattr(
        backup_health,
        "load_backup_status",
        lambda: {
            "last_backup_type":
                "EXTERNAL",
            "last_backup_path":
                r"D:\Northstar_Backups\2026-08-25",
            "last_external_success":
                "2026-08-25T09:00:00-04:00",
        },
    )

    data = (
        backup_health
        .build_backup_health_data(
            datetime(
                2026,
                8,
                25,
                9,
                30,
            )
        )
    )

    assert (
        data["drive_status"]
        == "CONNECTED"
    )

    assert (
        data["drive_health"]
        == "PASS"
    )

    assert (
        data["external_current"]
        is True
    )
