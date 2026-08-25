import mobile_dashboard.backup_health_ui as backup_ui


def sample_backup_data():
    return {
        "drive_status": "DISCONNECTED",
        "drive_health": "WARNING",
        "last_external": "Aug 24, 2026 4:10 PM",
        "backup_age": "17h 20m",
        "next_expected": "Aug 25, 2026 4:05 PM",
        "countdown": "6h 35m",
        "reminder": (
            "Connect SanDisk - next EOD "
            "backup in 6h 35m"
        ),
        "reminder_health": "WARNING",
        "last_backup_type": "LOCAL_FALLBACK",
        "last_backup_path": (
            r"C:\Northstar_Backups\2026-08-25"
        ),
        "local_fallback": "USED LAST BACKUP",
        "local_fallback_health": "WARNING",
        "external_root": (
            r"D:\Northstar_Backups"
        ),
    }


def test_render_backup_health_panel():
    html = backup_ui.render_backup_health_panel(
        sample_backup_data()
    )

    assert "Backup Health" in html
    assert "DISCONNECTED" in html
    assert "LOCAL_FALLBACK" in html
    assert "USED LAST BACKUP" in html
    assert "Connect SanDisk" in html


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
        updated.index("Backup Health")
        < updated.index("System Health")
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
