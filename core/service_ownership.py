"""
Northstar Trading Service Ownership

Provides a cross-process ownership lock so only one Northstar
process can control automatic trading services at a time.

The lock itself is authoritative. The JSON owner file is only
diagnostic information for health/status displays.
"""

import json
import msvcrt
import os
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

LOCK_FILE = (
    RUNTIME_FOLDER
    / "trading_services.lock"
)

OWNER_FILE = (
    RUNTIME_FOLDER
    / "trading_services_owner.json"
)


class TradingServiceOwnership:
    def __init__(self, owner_name):
        self.owner_name = str(owner_name)
        self.process_id = os.getpid()
        self.lock_handle = None
        self.acquired = False

    def acquire(self):
        if self.acquired:
            return True

        RUNTIME_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        lock_handle = open(
            LOCK_FILE,
            "a+b",
            buffering=0,
        )

        lock_handle.seek(
            0,
            os.SEEK_END,
        )

        if lock_handle.tell() == 0:
            lock_handle.write(b"\0")

        lock_handle.seek(0)

        try:
            msvcrt.locking(
                lock_handle.fileno(),
                msvcrt.LK_NBLCK,
                1,
            )

        except OSError:
            lock_handle.close()
            return False

        self.lock_handle = lock_handle
        self.acquired = True

        owner_state = {
            "owner": self.owner_name,
            "process_id": self.process_id,
            "acquired_at": datetime.now().isoformat(),
        }

        temporary_file = OWNER_FILE.with_suffix(
            ".tmp"
        )

        temporary_file.write_text(
            json.dumps(
                owner_state,
                indent=4,
            ),
            encoding="utf-8",
        )

        temporary_file.replace(
            OWNER_FILE
        )

        return True

    def release(self):
        if not self.acquired:
            return

        try:
            if OWNER_FILE.exists():
                try:
                    owner_state = json.loads(
                        OWNER_FILE.read_text(
                            encoding="utf-8",
                        )
                    )

                    if (
                        owner_state.get("process_id")
                        == self.process_id
                    ):
                        OWNER_FILE.unlink()

                except (
                    OSError,
                    json.JSONDecodeError,
                ):
                    pass

            self.lock_handle.seek(0)

            msvcrt.locking(
                self.lock_handle.fileno(),
                msvcrt.LK_UNLCK,
                1,
            )

        finally:
            if self.lock_handle is not None:
                self.lock_handle.close()

            self.lock_handle = None
            self.acquired = False


def read_trading_service_owner():
    if not OWNER_FILE.exists():
        return None

    try:
        return json.loads(
            OWNER_FILE.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None
