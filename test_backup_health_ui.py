import mobile_dashboard.backup_health_ui as backup_ui


def sample_backup_data():
    return {
        "drive_status": "DISCONNECTED - OK",
        "drive_health": "PASS",

        "last_external":
            "Aug 25, 2026 9:19 AM",

        "backup_age":
            "1d 0h 0m",

        "next_expected":
            "Sep 1, 2026 9:19 AM",

        "countdown":
            "6d 0h 0m",

        "reminder":
            "Physical backup due in 6d 0h 0m",

        "reminder_health": "PASS",

        "last_backup_type":
            "LOCAL_FALLBACK",

        "last_backup_path": (
            r"C:\Northstar_Backups\2026-08-25"
        ),

        "local_fallback":
            "DAILY LOCAL BACKUP OK",

        "local_fallback_health":
            "PASS",

        "cloud_backup_status":
            "PASS",

        "cloud_backup_health":
            "PASS",

        "last_cloud_backup":
            "Aug 25, 2026 9:56 AM",

        "cloud_backup_age":
            "4m",

        "next_cloud_backup":
            "Aug 25, 2026 4:05 PM",

        "cloud_backup_path": (
            r"C:\Users\Chris\OneDrive\Northstar_Cloud_Backups\northstar_critical.nsbackup"
        ),

        "restore_test_status":
            "PASS",

        "restore_test_health":
            "PASS",

        "last_restore_test":
            "Aug 25, 2026 9:35 AM",

        "last_successful_restore_test":
            "Aug 25, 2026 9:35 AM",

        "next_restore_test":
            "Sep 24, 2026 9:35 AM",

        "restore_test_countdown":
            "29d 23h 30m",

        "restore_test_backup_path": (
            r"D:\Northstar_Backups\2026-08-25"
        ),

        "external_root": (
            r"D:\Northstar_Backups"
        ),
    }


def test_render_backup_health_panel():
    html = (
        backup_ui
        .render_backup_health_panel(
            sample_backup_data()
        )
    )

    assert "Backup Health" in html

    assert (
        "DISCONNECTED - OK"
        in html
    )

    assert (
        "DAILY LOCAL BACKUP OK"
        in html
    )

    assert (
        "Encrypted Cloud Backup"
        in html
    )

    assert (
        "Last Cloud Backup"
        in html
    )

    assert (
        "Cloud Backup Age"
        in html
    )

    assert (
        "Next Cloud Backup Expected"
        in html
    )

    assert (
        "Aug 25, 2026 9:56 AM"
        in html
    )

    assert (
        "Restore Test Status"
        in html
    )

    assert (
        "Last Restore Test"
        in html
    )

    assert (
        "Next Restore Test Due"
        in html
    )

    assert (
        "Restore Test Countdown"
        in html
    )

    assert (
        "Sep 24, 2026 9:35 AM"
        in html
    )


def test_inject_before_system_health(
    monkeypatch,
):
    monkeypatch.setattr(
        backup_ui,
        "build_backup_health_data",
        sample_backup_data,
    )

    original = """
<html>
<body>
            <section class="health-card">
                <h2>System Health</h2>
            </section>
</body>
</html>
"""

    updated = (
        backup_ui
        .inject_backup_health_panel(
            original
        )
    )

    assert "Backup Health" in updated

    assert (
        updated.index(
            "Backup Health"
        )
        < updated.index(
            "System Health"
        )
    )


def test_injection_is_not_duplicated(
    monkeypatch,
):
    monkeypatch.setattr(
        backup_ui,
        "build_backup_health_data",
        sample_backup_data,
    )

    original = """
            <section class="health-card">
                <h2>System Health</h2>
            </section>
"""

    first = (
        backup_ui
        .inject_backup_health_panel(
            original
        )
    )

    second = (
        backup_ui
        .inject_backup_health_panel(
            first
        )
    )

    assert (
        second.count(
            'id="backup-health-panel"'
        )
        == 1
    )
