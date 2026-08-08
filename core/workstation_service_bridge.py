"""
Northstar Workstation Service Bridge

Allows the GUI to use local background-service threads when
the GUI owns the trading-service lock, while representing
headless-owned services with thread-like status proxies.

Importing this module does not start any services.
"""

from datetime import datetime
from pathlib import Path

from core.service_ownership import (
    TradingServiceOwnership,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

HEADLESS_HEARTBEAT_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "headless_runtime_heartbeat.txt"
)

HEADLESS_HEARTBEAT_MAX_AGE_SECONDS = 90

GUI_SERVICE_OWNERSHIP = (
    TradingServiceOwnership(
        "GUI_WORKSTATION"
    )
)


def read_headless_runtime_heartbeat():
    if not HEADLESS_HEARTBEAT_FILE.exists():
        return {}

    try:
        state = {}

        for line in (
            HEADLESS_HEARTBEAT_FILE
            .read_text(
                encoding="utf-8",
            )
            .splitlines()
        ):
            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1,
            )

            state[key.strip()] = value.strip()

        return state

    except OSError:
        return {}


def is_headless_service_running(
    service_key,
    max_age_seconds=(
        HEADLESS_HEARTBEAT_MAX_AGE_SECONDS
    ),
):
    state = read_headless_runtime_heartbeat()

    if state.get(service_key) != "RUNNING":
        return False

    heartbeat_time_text = state.get("time")

    if not heartbeat_time_text:
        return False

    try:
        heartbeat_time = datetime.fromisoformat(
            heartbeat_time_text
        )

    except ValueError:
        return False

    if heartbeat_time.tzinfo is None:
        current_time = datetime.now()
    else:
        current_time = datetime.now(
            heartbeat_time.tzinfo
        )

    heartbeat_age = (
        current_time - heartbeat_time
    ).total_seconds()

    return (
        -5.0
        <= heartbeat_age
        <= max_age_seconds
    )


class HeadlessServiceThreadProxy:
    """
    Thread-like status object used by the GUI when a service is
    owned by the independent headless runtime.
    """

    def __init__(self, service_key):
        self.service_key = service_key

    def is_alive(self):
        return is_headless_service_running(
            self.service_key
        )


def build_workstation_service_starter(
    start_function,
    service_key,
):
    """
    Wrap an existing service starter with ownership protection.

    If the GUI owns or can acquire the trading-service lock,
    start the normal local service.

    If another process owns the lock, return a thread-like proxy
    representing the corresponding headless service instead.
    """

    def start_service(
        *args,
        **kwargs,
    ):
        gui_owns_services = (
            GUI_SERVICE_OWNERSHIP.acquired
            or GUI_SERVICE_OWNERSHIP.acquire()
        )

        if gui_owns_services:
            return start_function(
                *args,
                **kwargs,
            )

        return HeadlessServiceThreadProxy(
            service_key
        )

    return start_service
