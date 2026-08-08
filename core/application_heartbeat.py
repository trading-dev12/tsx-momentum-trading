"""
Northstar application heartbeat state.

Tracks whether the previous Northstar workstation session
ended cleanly or disappeared unexpectedly.

This cannot prove that a power outage occurred. An unexpected
gap may also be caused by a crash, forced restart, or process
termination.
"""

import json
from datetime import datetime
from pathlib import Path

from core.market_hours import TORONTO_TIMEZONE


HEARTBEAT_STATE_FILE = Path(
    "data/runtime/application_heartbeat.json"
)


def load_application_heartbeat(
    state_file=HEARTBEAT_STATE_FILE,
):
    """
    Load persistent application heartbeat state.
    """

    state_file = Path(state_file)

    if not state_file.exists():
        return {
            "session_active": False,
            "last_heartbeat": None,
            "clean_shutdown": True,
        }

    try:
        with state_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            state = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {
            "session_active": False,
            "last_heartbeat": None,
            "clean_shutdown": True,
        }

    return {
        "session_active": bool(
            state.get(
                "session_active",
                False,
            )
        ),
        "last_heartbeat": state.get(
            "last_heartbeat"
        ),
        "clean_shutdown": bool(
            state.get(
                "clean_shutdown",
                True,
            )
        ),
    }


def save_application_heartbeat(
    state,
    state_file=HEARTBEAT_STATE_FILE,
):
    """
    Persist application heartbeat state.
    """

    state_file = Path(state_file)

    state_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with state_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=4,
        )


def record_application_start(
    current_datetime=None,
    state_file=HEARTBEAT_STATE_FILE,
):
    """
    Start a new workstation session.

    Returns whether the prior session appears to have ended
    unexpectedly.
    """

    if current_datetime is None:
        current_datetime = datetime.now(
            TORONTO_TIMEZONE
        )

    previous_state = (
        load_application_heartbeat(
            state_file=state_file,
        )
    )

    unexpected_restart = (
        previous_state["session_active"]
        and not previous_state[
            "clean_shutdown"
        ]
        and previous_state[
            "last_heartbeat"
        ]
        is not None
    )

    downtime_seconds = None

    if unexpected_restart:
        try:
            previous_heartbeat = (
                datetime.fromisoformat(
                    previous_state[
                        "last_heartbeat"
                    ]
                )
            )

            downtime_seconds = max(
                0,
                int(
                    (
                        current_datetime
                        - previous_heartbeat
                    ).total_seconds()
                ),
            )

        except (
            TypeError,
            ValueError,
        ):
            downtime_seconds = None

    new_state = {
        "session_active": True,
        "last_heartbeat": (
            current_datetime.isoformat()
        ),
        "clean_shutdown": False,
    }

    save_application_heartbeat(
        new_state,
        state_file=state_file,
    )

    return {
        "transition": (
            "UNEXPECTED_RESTART"
            if unexpected_restart
            else "STARTED"
        ),
        "downtime_seconds": downtime_seconds,
        "previous_last_heartbeat": (
            previous_state[
                "last_heartbeat"
            ]
        ),
    }


def record_application_heartbeat(
    current_datetime=None,
    state_file=HEARTBEAT_STATE_FILE,
):
    """
    Update the heartbeat for the active workstation session.
    """

    if current_datetime is None:
        current_datetime = datetime.now(
            TORONTO_TIMEZONE
        )

    state = (
        load_application_heartbeat(
            state_file=state_file,
        )
    )

    state["session_active"] = True
    state["clean_shutdown"] = False
    state["last_heartbeat"] = (
        current_datetime.isoformat()
    )

    save_application_heartbeat(
        state,
        state_file=state_file,
    )

    return state


def record_clean_shutdown(
    current_datetime=None,
    state_file=HEARTBEAT_STATE_FILE,
):
    """
    Mark the workstation session as intentionally closed.
    """

    if current_datetime is None:
        current_datetime = datetime.now(
            TORONTO_TIMEZONE
        )

    state = (
        load_application_heartbeat(
            state_file=state_file,
        )
    )

    state["session_active"] = False
    state["clean_shutdown"] = True
    state["last_heartbeat"] = (
        current_datetime.isoformat()
    )

    save_application_heartbeat(
        state,
        state_file=state_file,
    )

    return state