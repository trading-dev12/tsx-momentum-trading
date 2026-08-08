from datetime import datetime

from core.market_hours import TORONTO_TIMEZONE
from core.application_heartbeat import (
    load_application_heartbeat,
    record_application_start,
    record_application_heartbeat,
    record_clean_shutdown,
)


def test_first_start_is_normal(tmp_path):
    state_file = (
        tmp_path
        / "application_heartbeat.json"
    )

    result = record_application_start(
        current_datetime=datetime(
            2026,
            8,
            7,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    assert result["transition"] == "STARTED"
    assert result["downtime_seconds"] is None

    state = load_application_heartbeat(
        state_file=state_file,
    )

    assert state["session_active"] is True
    assert state["clean_shutdown"] is False


def test_heartbeat_updates_active_session(tmp_path):
    state_file = (
        tmp_path
        / "application_heartbeat.json"
    )

    record_application_start(
        current_datetime=datetime(
            2026,
            8,
            7,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    state = record_application_heartbeat(
        current_datetime=datetime(
            2026,
            8,
            7,
            8,
            5,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    assert state["session_active"] is True
    assert state["clean_shutdown"] is False

    assert state["last_heartbeat"].startswith(
        "2026-08-07T08:05:00"
    )


def test_clean_shutdown_does_not_trigger_restart_warning(
    tmp_path,
):
    state_file = (
        tmp_path
        / "application_heartbeat.json"
    )

    record_application_start(
        current_datetime=datetime(
            2026,
            8,
            7,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    record_clean_shutdown(
        current_datetime=datetime(
            2026,
            8,
            7,
            16,
            30,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    result = record_application_start(
        current_datetime=datetime(
            2026,
            8,
            8,
            8,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    assert result["transition"] == "STARTED"
    assert result["downtime_seconds"] is None


def test_unexpected_restart_reports_downtime(
    tmp_path,
):
    state_file = (
        tmp_path
        / "application_heartbeat.json"
    )

    record_application_start(
        current_datetime=datetime(
            2026,
            8,
            7,
            9,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    record_application_heartbeat(
        current_datetime=datetime(
            2026,
            8,
            7,
            10,
            0,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    result = record_application_start(
        current_datetime=datetime(
            2026,
            8,
            7,
            10,
            15,
            tzinfo=TORONTO_TIMEZONE,
        ),
        state_file=state_file,
    )

    assert (
        result["transition"]
        == "UNEXPECTED_RESTART"
    )

    assert result["downtime_seconds"] == 900

    assert (
        result["previous_last_heartbeat"]
        is not None
    )