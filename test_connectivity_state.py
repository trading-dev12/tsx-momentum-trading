from datetime import datetime, timedelta, timezone

import core.connectivity_state as connectivity_state


def test_initial_online_state(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "connectivity_state.json"
    )

    monkeypatch.setattr(
        connectivity_state,
        "CONNECTIVITY_STATE_FILE",
        state_file,
    )

    now = datetime(
        2026,
        8,
        7,
        9,
        0,
        tzinfo=timezone.utc,
    )

    result = (
        connectivity_state
        .record_connectivity_status(
            True,
            now=now,
        )
    )

    assert result["transition"] == "INITIAL_ONLINE"
    assert result["status"] == "ONLINE"

    saved = (
        connectivity_state
        .load_connectivity_state()
    )

    assert saved["status"] == "ONLINE"
    assert saved["outage_started_at"] is None


def test_outage_is_recorded_only_once(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "connectivity_state.json"
    )

    monkeypatch.setattr(
        connectivity_state,
        "CONNECTIVITY_STATE_FILE",
        state_file,
    )

    outage_start = datetime(
        2026,
        8,
        7,
        14,
        0,
        tzinfo=timezone.utc,
    )

    first_result = (
        connectivity_state
        .record_connectivity_status(
            False,
            now=outage_start,
        )
    )

    assert (
        first_result["transition"]
        == "OUTAGE_STARTED"
    )

    first_start_text = (
        first_result["outage_started_at"]
    )

    second_result = (
        connectivity_state
        .record_connectivity_status(
            False,
            now=(
                outage_start
                + timedelta(minutes=5)
            ),
        )
    )

    assert second_result["transition"] == "NONE"
    assert (
        second_result["outage_started_at"]
        == first_start_text
    )

    saved = (
        connectivity_state
        .load_connectivity_state()
    )

    assert saved["status"] == "OFFLINE"
    assert (
        saved["outage_started_at"]
        == first_start_text
    )


def test_recovery_reports_downtime(
    monkeypatch,
    tmp_path,
):
    state_file = (
        tmp_path
        / "connectivity_state.json"
    )

    monkeypatch.setattr(
        connectivity_state,
        "CONNECTIVITY_STATE_FILE",
        state_file,
    )

    outage_start = datetime(
        2026,
        8,
        7,
        14,
        0,
        tzinfo=timezone.utc,
    )

    recovery_time = (
        outage_start
        + timedelta(
            minutes=12,
            seconds=30,
        )
    )

    connectivity_state.record_connectivity_status(
        False,
        now=outage_start,
    )

    result = (
        connectivity_state
        .record_connectivity_status(
            True,
            now=recovery_time,
        )
    )

    assert result["transition"] == "RECOVERED"
    assert result["status"] == "ONLINE"
    assert result["downtime_seconds"] == 750
    assert (
        result["recovered_at"]
        == recovery_time.isoformat()
    )

    saved = (
        connectivity_state
        .load_connectivity_state()
    )

    assert saved["status"] == "ONLINE"
    assert saved["outage_started_at"] is None