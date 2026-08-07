import core.ibkr_health_monitor as ibkr_health


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


def test_ibkr_tws_available(
    monkeypatch,
):
    calls = []

    def fake_create_connection(
        address,
        timeout,
    ):
        calls.append(
            {
                "address": address,
                "timeout": timeout,
            }
        )

        return FakeConnection()

    monkeypatch.setattr(
        ibkr_health.socket,
        "create_connection",
        fake_create_connection,
    )

    result = (
        ibkr_health
        .check_ibkr_tws_available()
    )

    assert result["available"] is True
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 7496
    assert result["error"] is None

    assert calls == [
        {
            "address": (
                "127.0.0.1",
                7496,
            ),
            "timeout": 1.0,
        }
    ]


def test_ibkr_tws_unavailable(
    monkeypatch,
):
    def fake_create_connection(
        address,
        timeout,
    ):
        raise ConnectionRefusedError(
            "TWS API unavailable"
        )

    monkeypatch.setattr(
        ibkr_health.socket,
        "create_connection",
        fake_create_connection,
    )

    result = (
        ibkr_health
        .check_ibkr_tws_available()
    )

    assert result["available"] is False
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 7496
    assert "TWS API unavailable" in result["error"]