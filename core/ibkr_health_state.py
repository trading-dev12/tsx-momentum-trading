"""
Persistent IBKR/TWS health state for Northstar.

Tracks TWS availability transitions without containing
trading-strategy logic.
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

IBKR_HEALTH_STATE_FILE = (
    RUNTIME_FOLDER
    / "ibkr_health_state.json"
)


def get_default_ibkr_health_state():
    return {
        "status": "UNKNOWN",
        "unavailable_started_at": None,
    }


def load_ibkr_health_state():
    if not IBKR_HEALTH_STATE_FILE.exists():
        return get_default_ibkr_health_state()

    try:
        data = json.loads(
            IBKR_HEALTH_STATE_FILE.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return get_default_ibkr_health_state()

    if not isinstance(data, dict):
        return get_default_ibkr_health_state()

    return {
        "status": data.get(
            "status",
            "UNKNOWN",
        ),
        "unavailable_started_at": data.get(
            "unavailable_started_at",
        ),
    }


def save_ibkr_health_state(state):
    RUNTIME_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    IBKR_HEALTH_STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
        ),
        encoding="utf-8",
    )


def record_ibkr_tws_status(
    available,
    now=None,
):
    """
    Record a TWS availability observation and return any
    state transition that occurred.
    """

    if not isinstance(available, bool):
        raise ValueError(
            "available must be True or False."
        )

    if now is None:
        now = datetime.now().astimezone()

    state = load_ibkr_health_state()

    previous_status = state.get(
        "status",
        "UNKNOWN",
    )

    now_text = now.isoformat()

    result = {
        "transition": "NONE",
        "previous_status": previous_status,
        "status": previous_status,
        "unavailable_started_at": state.get(
            "unavailable_started_at"
        ),
        "recovered_at": None,
        "downtime_seconds": None,
    }

    if available is False:
        if previous_status != "UNAVAILABLE":
            state = {
                "status": "UNAVAILABLE",
                "unavailable_started_at": now_text,
            }

            save_ibkr_health_state(
                state
            )

            result.update(
                {
                    "transition": "TWS_DOWN",
                    "status": "UNAVAILABLE",
                    "unavailable_started_at": now_text,
                }
            )

        return result

    if previous_status == "UNAVAILABLE":
        unavailable_started_at = state.get(
            "unavailable_started_at"
        )

        downtime_seconds = None

        if unavailable_started_at:
            try:
                unavailable_start = (
                    datetime.fromisoformat(
                        unavailable_started_at
                    )
                )

                downtime_seconds = max(
                    0,
                    int(
                        (
                            now - unavailable_start
                        ).total_seconds()
                    ),
                )

            except ValueError:
                downtime_seconds = None

        state = {
            "status": "AVAILABLE",
            "unavailable_started_at": None,
        }

        save_ibkr_health_state(
            state
        )

        result.update(
            {
                "transition": "TWS_RECOVERED",
                "status": "AVAILABLE",
                "recovered_at": now_text,
                "downtime_seconds": downtime_seconds,
            }
        )

        return result

    if previous_status != "AVAILABLE":
        state = {
            "status": "AVAILABLE",
            "unavailable_started_at": None,
        }

        save_ibkr_health_state(
            state
        )

        result.update(
            {
                "transition": "INITIAL_AVAILABLE",
                "status": "AVAILABLE",
            }
        )

    return result