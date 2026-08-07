import core.connectivity_monitor as connectivity_monitor


class FakeConnection:
    """
    Minimal context manager representing a successful socket.
    """

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


def test_connectivity_online_first_target(
    monkeypatch,
):
    """
    Internet should be ONLINE when the first external target
    can be reached.
    """

    calls = []

    def fake_create_connection(
        address,
        timeout,
    ):
        calls.append(
            (address, timeout)
        )

        return FakeConnection()

    monkeypatch.setattr(
        connectivity_monitor.socket,
        "create_connection",
        fake_create_connection,
    )

    result = (
        connectivity_monitor
        .check_internet_connectivity()
    )

    assert result["online"] is True
    assert (
        result["reachable_target"]
        == "Cloudflare"
    )
    assert result["failures"] == []
    assert len(calls) == 1


def test_connectivity_uses_second_target(
    monkeypatch,
):
    """
    Failure of one external target must not be treated as a
    complete internet outage when another target is reachable.
    """

    calls = []

    def fake_create_connection(
        address,
        timeout,
    ):
        calls.append(
            (address, timeout)
        )

        if len(calls) == 1:
            raise OSError(
                "First target unavailable"
            )

        return FakeConnection()

    monkeypatch.setattr(
        connectivity_monitor.socket,
        "create_connection",
        fake_create_connection,
    )

    result = (
        connectivity_monitor
        .check_internet_connectivity()
    )

    assert result["online"] is True
    assert (
        result["reachable_target"]
        == "Google DNS"
    )
    assert len(result["failures"]) == 1
    assert (
        result["failures"][0]["target"]
        == "Cloudflare"
    )
    assert len(calls) == 2


def test_connectivity_reports_full_outage(
    monkeypatch,
):
    """
    Internet should be OFFLINE only when every configured
    external target fails.
    """

    calls = []

    def fake_create_connection(
        address,
        timeout,
    ):
        calls.append(
            (address, timeout)
        )

        raise OSError(
            "Network unreachable"
        )

    monkeypatch.setattr(
        connectivity_monitor.socket,
        "create_connection",
        fake_create_connection,
    )

    result = (
        connectivity_monitor
        .check_internet_connectivity()
    )

    assert result["online"] is False
    assert result["reachable_target"] is None
    assert len(result["failures"]) == 2
    assert len(calls) == 2