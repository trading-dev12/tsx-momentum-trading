from datetime import datetime, timedelta, timezone

import core.ibkr_health_state as ibkr_health_state


def test_initial_available_state(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "ibkr_health_state.json"
    )

    monkeypatch.setattr(
        ibkr_health_state,
        "IBKR_HEALTH_STATE_FILE",
        state_file,
    )

    now = datetime(
        2026,
        8,
        7,
        13,
        30,
        tzinfo=timezone.utc,
    )

    result = (
        ibkr_health_state
        .record_ibkr_tws_status(
            True,
            now=now,
        )
    )

    assert (
        result["transition"]
        == "INITIAL_AVAILABLE"
    )

    assert result["status"] == "AVAILABLE"

    saved = (
        ibkr_health_state
        .load_ibkr_health_state()
    )

    assert saved["status"] == "AVAILABLE"
    assert (
        saved["unavailable_started_at"]
        is None
    )


def test_tws_down_is_recorded_only_once(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "ibkr_health_state.json"
    )

    monkeypatch.setattr(
        ibkr_health_state,
        "IBKR_HEALTH_STATE_FILE",
        state_file,
    )

    down_time = datetime(
        2026,
        8,
        7,
        14,
        0,
        tzinfo=timezone.utc,
    )

    first_result = (
        ibkr_health_state
        .record_ibkr_tws_status(
            False,
            now=down_time,
        )
    )

    assert (
        first_result["transition"]
        == "TWS_DOWN"
    )

    first_start = (
        first_result[
            "unavailable_started_at"
        ]
    )

    second_result = (
        ibkr_health_state
        .record_ibkr_tws_status(
            False,
            now=(
                down_time
                + timedelta(minutes=5)
            ),
        )
    )

    assert second_result["transition"] == "NONE"

    assert (
        second_result[
            "unavailable_started_at"
        ]
        == first_start
    )


def test_tws_recovery_reports_downtime(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "ibkr_health_state.json"
    )

    monkeypatch.setattr(
        ibkr_health_state,
        "IBKR_HEALTH_STATE_FILE",
        state_file,
    )

    down_time = datetime(
        2026,
        8,
        7,
        14,
        0,
        tzinfo=timezone.utc,
    )

    recovery_time = (
        down_time
        + timedelta(
            minutes=7,
            seconds=15,
        )
    )

    ibkr_health_state.record_ibkr_tws_status(
        False,
        now=down_time,
    )

    result = (
        ibkr_health_state
        .record_ibkr_tws_status(
            True,
            now=recovery_time,
        )
    )

    assert (
        result["transition"]
        == "TWS_RECOVERED"
    )

    assert result["status"] == "AVAILABLE"
    assert result["downtime_seconds"] == 435

    assert (
        result["recovered_at"]
        == recovery_time.isoformat()
    )

    saved = (
        ibkr_health_state
        .load_ibkr_health_state()
    )

    assert saved["status"] == "AVAILABLE"

    assert (
        saved["unavailable_started_at"]
        is None
    )