"""
Northstar Headless Runtime

Runs essential non-GUI Northstar services so the system can
recover after a Windows reboot without requiring desktop login.

Current services:
- Runtime heartbeat
- Mobile dashboard

Trading, execution, scanner, and EOD services are NOT enabled yet.
"""

import getpass
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

HEARTBEAT_FILE = (
    RUNTIME_FOLDER
    / "headless_runtime_heartbeat.txt"
)


def is_dashboard_running(
    host="127.0.0.1",
    port=5000,
):
    try:
        with socket.create_connection(
            (host, port),
            timeout=1.0,
        ):
            return True
    except OSError:
        return False


def start_dashboard():
    if is_dashboard_running():
        return None

    command = [
        sys.executable,
        "-m",
        "waitress",
        "--listen=0.0.0.0:5000",
        "mobile_dashboard.app:app",
    ]

    startup_info = None
    creation_flags = 0

    if sys.platform == "win32":
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= (
            subprocess.STARTF_USESHOWWINDOW
        )
        creation_flags = subprocess.CREATE_NO_WINDOW

    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startup_info,
        creationflags=creation_flags,
    )


def write_heartbeat(
    dashboard_process=None,
    dashboard_error="",
):
    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    dashboard_running = (
        is_dashboard_running()
    )

    dashboard_pid = ""

    if (
        dashboard_process is not None
        and dashboard_process.poll() is None
    ):
        dashboard_pid = str(
            dashboard_process.pid
        )

    HEARTBEAT_FILE.write_text(
        (
            "NORTHSTAR HEADLESS RUNTIME\n"
            f"time={datetime.now().isoformat()}\n"
            f"user={getpass.getuser()}\n"
            "status=RUNNING\n"
            f"dashboard_status="
            f"{'RUNNING' if dashboard_running else 'STOPPED'}\n"
            f"dashboard_pid={dashboard_pid}\n"
            f"dashboard_error={dashboard_error}\n"
        ),
        encoding="utf-8",
    )


def main():
    dashboard_process = None
    dashboard_error = ""

    while True:
        if not is_dashboard_running():
            try:
                dashboard_process = (
                    start_dashboard()
                )
                dashboard_error = ""
            except Exception as error:
                dashboard_error = str(error)

        write_heartbeat(
            dashboard_process=dashboard_process,
            dashboard_error=dashboard_error,
        )

        time.sleep(30)


if __name__ == "__main__":
    main()
