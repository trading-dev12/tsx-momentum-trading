"""
Persistent connectivity outage state for Northstar.

This module records internet outage and recovery transitions.
It contains no trading-strategy logic.
"""

import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

CONNECTIVITY_STATE_FILE = (
    RUNTIME_FOLDER
    / "connectivity_state.json"
)


def get_default_connectivity_state():
    return {
        "status": "UNKNOWN",
        "outage_started_at": None,
    }


def load_connectivity_state():
    if not CONNECTIVITY_STATE_FILE.exists():
        return get_default_connectivity_state()

    try:
        data = json.loads(
            CONNECTIVITY_STATE_FILE.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return get_default_connectivity_state()

    if not isinstance(data, dict):
        return get_default_connectivity_state()

    return {
        "status": data.get(
            "status",
            "UNKNOWN",
        ),
        "outage_started_at": data.get(
            "outage_started_at",
        ),
    }


def save_connectivity_state(state):
    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    CONNECTIVITY_STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
        ),
        encoding="utf-8",
    )


def record_connectivity_status(
    online,
    now=None,
):
    """
    Record an ONLINE/OFFLINE observation and return any state
    transition that occurred.
    """

    if not isinstance(online, bool):
        raise ValueError(
            "online must be True or False."
        )

    if now is None:
        now = datetime.now().astimezone()

    state = load_connectivity_state()

    previous_status = state.get(
        "status",
        "UNKNOWN",
    )

    now_text = now.isoformat()

    result = {
        "transition": "NONE",
        "previous_status": previous_status,
        "status": previous_status,
        "outage_started_at": state.get(
            "outage_started_at"
        ),
        "recovered_at": None,
        "downtime_seconds": None,
    }

    if online is False:
        if previous_status != "OFFLINE":
            state = {
                "status": "OFFLINE",
                "outage_started_at": now_text,
            }

            save_connectivity_state(
                state
            )

            result.update(
                {
                    "transition": "OUTAGE_STARTED",
                    "status": "OFFLINE",
                    "outage_started_at": now_text,
                }
            )

        return result

    if previous_status == "OFFLINE":
        outage_started_at = state.get(
            "outage_started_at"
        )

        downtime_seconds = None

        if outage_started_at:
            try:
                outage_start = (
                    datetime.fromisoformat(
                        outage_started_at
                    )
                )

                downtime_seconds = max(
                    0,
                    int(
                        (
                            now - outage_start
                        ).total_seconds()
                    ),
                )

            except ValueError:
                downtime_seconds = None

        state = {
            "status": "ONLINE",
            "outage_started_at": None,
        }

        save_connectivity_state(
            state
        )

        result.update(
            {
                "transition": "RECOVERED",
                "status": "ONLINE",
                "recovered_at": now_text,
                "downtime_seconds": downtime_seconds,
            }
        )

        return result

    if previous_status != "ONLINE":
        state = {
            "status": "ONLINE",
            "outage_started_at": None,
        }

        save_connectivity_state(
            state
        )

        result.update(
            {
                "transition": "INITIAL_ONLINE",
                "status": "ONLINE",
            }
        )

    return result