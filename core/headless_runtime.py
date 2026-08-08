"""
Northstar Headless Runtime

Runs essential non-GUI Northstar services so the system can
recover after a Windows reboot without requiring desktop login.

The mobile dashboard always runs.

Trading services are enabled only when:
data/runtime/enable_headless_trading.flag

exists when this process starts.
"""

import getpass
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from core.headless_service_coordinator import (
    run_headless_market_cycle,
)
from core.headless_trading_services import (
    get_headless_service_status,
    start_headless_trading_services,
)
from core.service_ownership import (
    TradingServiceOwnership,
)


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

TRADING_ENABLE_FLAG = (
    RUNTIME_FOLDER
    / "enable_headless_trading.flag"
)

MARKET_CYCLE_INTERVAL_SECONDS = 300


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
        creation_flags = (
            subprocess.CREATE_NO_WINDOW
        )

    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startup_info,
        creationflags=creation_flags,
    )


def is_headless_trading_enabled(
    flag_file=TRADING_ENABLE_FLAG,
):
    return flag_file.exists()


def write_heartbeat(
    dashboard_process=None,
    dashboard_error="",
    trading_services_enabled=False,
    trading_services_owned=False,
    execution_status="DISABLED",
    eod_status="DISABLED",
    market_services_status="DISABLED",
    market_cycle_status="DISABLED",
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
            f"trading_services_enabled="
            f"{'YES' if trading_services_enabled else 'NO'}\n"
            f"trading_services_lock="
            f"{'OWNED' if trading_services_owned else 'NOT_OWNED'}\n"
            f"execution_status={execution_status}\n"
            f"eod_status={eod_status}\n"
            f"market_services_status="
            f"{market_services_status}\n"
            f"market_cycle_status="
            f"{market_cycle_status}\n"
        ),
        encoding="utf-8",
    )


def start_market_cycle_thread(
    engines,
    refresh_id,
    market_cycle_state,
):
    def worker():
        market_cycle_state[
            "status"
        ] = "RUNNING"

        try:
            result = run_headless_market_cycle(
                engines=engines,
                refresh_id=refresh_id,
            )

            market_cycle_state[
                "status"
            ] = result.get(
                "status",
                "COMPLETED",
            )

        except Exception as error:
            market_cycle_state[
                "status"
            ] = (
                "ERROR: "
                f"{error}"
            )

    thread = threading.Thread(
        target=worker,
        daemon=True,
        name="headless-market-cycle",
    )

    thread.start()

    return thread


def main():
    dashboard_process = None
    dashboard_error = ""

    trading_enabled = (
        is_headless_trading_enabled()
    )

    trading_service_ownership = (
        TradingServiceOwnership(
            "HEADLESS_RUNTIME"
        )
    )

    service_bundle = None
    market_cycle_thread = None
    market_cycle_refresh_id = 0
    last_market_cycle_start = 0.0

    market_cycle_state = {
        "status": (
            "IDLE"
            if trading_enabled
            else "DISABLED"
        ),
    }

    try:
        while True:
            execution_status = (
                "DISABLED"
            )

            eod_status = (
                "DISABLED"
            )

            market_services_status = (
                "DISABLED"
            )

            if trading_enabled:
                if (
                    not
                    trading_service_ownership.acquired
                ):
                    trading_service_ownership.acquire()

                if (
                    trading_service_ownership.acquired
                    and service_bundle is None
                ):
                    service_bundle = (
                        start_headless_trading_services()
                    )

                if service_bundle is None:
                    execution_status = (
                        "WAITING_FOR_LOCK"
                    )
                    eod_status = (
                        "WAITING_FOR_LOCK"
                    )
                    market_services_status = (
                        "WAITING_FOR_LOCK"
                    )

                else:
                    service_status = (
                        get_headless_service_status(
                            service_bundle
                        )
                    )

                    execution_status = (
                        service_status[
                            "execution_status"
                        ]
                    )

                    eod_status = (
                        service_status[
                            "eod_status"
                        ]
                    )

                    market_services_status = (
                        "RUNNING"
                    )

                    if (
                        execution_status
                        != "RUNNING"
                        or eod_status
                        != "RUNNING"
                    ):
                        raise RuntimeError(
                            "A headless trading "
                            "worker stopped."
                        )

                    current_monotonic = (
                        time.monotonic()
                    )

                    cycle_due = (
                        last_market_cycle_start == 0.0
                        or (
                            current_monotonic
                            - last_market_cycle_start
                        )
                        >= MARKET_CYCLE_INTERVAL_SECONDS
                    )

                    cycle_running = (
                        market_cycle_thread
                        is not None
                        and
                        market_cycle_thread.is_alive()
                    )

                    if (
                        cycle_due
                        and not cycle_running
                    ):
                        market_cycle_refresh_id += 1

                        market_cycle_thread = (
                            start_market_cycle_thread(
                                engines=(
                                    service_bundle[
                                        "engines"
                                    ]
                                ),
                                refresh_id=(
                                    market_cycle_refresh_id
                                ),
                                market_cycle_state=(
                                    market_cycle_state
                                ),
                            )
                        )

                        last_market_cycle_start = (
                            current_monotonic
                        )

            if not is_dashboard_running():
                try:
                    dashboard_process = (
                        start_dashboard()
                    )
                    dashboard_error = ""
                except Exception as error:
                    dashboard_error = str(
                        error
                    )

            write_heartbeat(
                dashboard_process=(
                    dashboard_process
                ),
                dashboard_error=(
                    dashboard_error
                ),
                trading_services_enabled=(
                    trading_enabled
                ),
                trading_services_owned=(
                    trading_service_ownership.acquired
                ),
                execution_status=(
                    execution_status
                ),
                eod_status=(
                    eod_status
                ),
                market_services_status=(
                    market_services_status
                ),
                market_cycle_status=(
                    market_cycle_state[
                        "status"
                    ]
                ),
            )

            time.sleep(30)

    finally:
        trading_service_ownership.release()


if __name__ == "__main__":
    main()
