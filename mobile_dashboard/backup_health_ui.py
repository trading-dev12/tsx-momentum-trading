from html import escape

from mobile_dashboard.backup_health import (
    build_backup_health_data,
)


def health_class(status):
    normalized = str(status).upper()

    if normalized == "PASS":
        return "health-pass"

    if normalized == "WARNING":
        return "health-warning"

    return "health-fail"


def render_backup_health_panel(
    data=None,
):
    if data is None:
        data = build_backup_health_data()

    drive_class = health_class(
        data["drive_health"]
    )

    reminder_class = health_class(
        data["reminder_health"]
    )

    fallback_class = health_class(
        data["local_fallback_health"]
    )

    cloud_class = health_class(
        data["cloud_backup_health"]
    )

    restore_class = health_class(
        data["restore_test_health"]
    )

    return f"""
    <section class="health-card"
             id="backup-health-panel">

        <h2>Backup Health</h2>

        <div class="health-grid">

            <div class="health-item">
                <div class="health-label">
                    Physical Backup Drive
                </div>

                <div class="health-value {drive_class}">
                    {escape(data["drive_status"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Last Physical Backup
                </div>

                <div class="health-value">
                    {escape(data["last_external"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Physical Backup Age
                </div>

                <div class="health-value">
                    {escape(data["backup_age"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Next Physical Backup Due
                </div>

                <div class="health-value">
                    {escape(data["next_expected"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Physical Backup Countdown
                </div>

                <div class="health-value {reminder_class}">
                    {escape(data["countdown"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Daily Local Backup
                </div>

                <div class="health-value {fallback_class}">
                    {escape(data["local_fallback"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Last Daily Backup Destination
                </div>

                <div class="health-value">
                    {escape(data["last_backup_type"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Reminder
                </div>

                <div class="health-value {reminder_class}">
                    {escape(data["reminder"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Encrypted Cloud Backup
                </div>

                <div class="health-value {cloud_class}">
                    {escape(data["cloud_backup_status"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Last Cloud Backup
                </div>

                <div class="health-value">
                    {escape(data["last_cloud_backup"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Cloud Backup Age
                </div>

                <div class="health-value">
                    {escape(data["cloud_backup_age"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Next Cloud Backup Expected
                </div>

                <div class="health-value">
                    {escape(data["next_cloud_backup"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Restore Test Status
                </div>

                <div class="health-value {restore_class}">
                    {escape(data["restore_test_status"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Last Restore Test
                </div>

                <div class="health-value">
                    {escape(data["last_restore_test"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Next Restore Test Due
                </div>

                <div class="health-value">
                    {escape(data["next_restore_test"])}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Restore Test Countdown
                </div>

                <div class="health-value {restore_class}">
                    {escape(data["restore_test_countdown"])}
                </div>
            </div>

        </div>

        <div class="footer">
            Physical destination:
            {escape(data["external_root"])}
        </div>

    </section>
    """


def inject_backup_health_panel(
    html,
):
    """
    Insert Backup Health immediately before
    the existing System Health section.
    """

    if (
        'id="backup-health-panel"'
        in html
    ):
        return html

    marker = """
            <section class="health-card">
                <h2>System Health</h2>
"""

    if marker not in html:
        return html

    panel = render_backup_health_panel()

    return html.replace(
        marker,
        panel + marker,
        1,
    )
