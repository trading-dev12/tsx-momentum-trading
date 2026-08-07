import time

import core.market_data as market_data


def build_test_quote(symbol, live_quote=None):
    """
    Return a minimal scanner quote for reconnect tests.
    """

    price = (
        live_quote["price"]
        if live_quote is not None
        else 99.0
    )

    return {
        "symbol": symbol,
        "price": price,
        "decision": "READY",
        "tmqs": 100,
        "confidence_score": 100,
    }


def test_ibkr_succeeds_on_first_attempt(
    monkeypatch,
):
    """
    A healthy IBKR connection should require only one attempt.
    """

    class FakeProvider:
        attempts = 0
        disconnects = 0

        def __init__(self, client_id):
            self.client_id = client_id

        def get_quotes(self, symbols):
            FakeProvider.attempts += 1

            return (
                {
                    "RY.TO": {
                        "price": 100.0,
                    },
                },
                {},
            )

        def disconnect(self):
            FakeProvider.disconnects += 1

    monkeypatch.setattr(
        market_data,
        "IBKRDataProvider",
        FakeProvider,
    )

    monkeypatch.setattr(
        market_data,
        "get_live_quote",
        build_test_quote,
    )

    results = market_data.get_quotes(
        ["RY.TO"]
    )

    assert FakeProvider.attempts == 1
    assert FakeProvider.disconnects == 1
    assert results[0]["price"] == 100.0


def test_ibkr_reconnects_after_temporary_failure(
    monkeypatch,
):
    """
    A temporary IBKR failure should automatically retry and
    recover without restarting the scanner.
    """

    sleep_calls = []

    monkeypatch.setattr(
        time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    class FakeProvider:
        attempts = 0
        disconnects = 0

        def __init__(self, client_id):
            self.client_id = client_id

        def get_quotes(self, symbols):
            FakeProvider.attempts += 1

            if FakeProvider.attempts == 1:
                raise ConnectionError(
                    "Temporary IBKR disconnect"
                )

            return (
                {
                    "RY.TO": {
                        "price": 101.0,
                    },
                },
                {},
            )

        def disconnect(self):
            FakeProvider.disconnects += 1

    monkeypatch.setattr(
        market_data,
        "IBKRDataProvider",
        FakeProvider,
    )

    monkeypatch.setattr(
        market_data,
        "get_live_quote",
        build_test_quote,
    )

    results = market_data.get_quotes(
        ["RY.TO"]
    )

    assert FakeProvider.attempts == 2
    assert FakeProvider.disconnects == 2
    assert sleep_calls == [2]
    assert results[0]["price"] == 101.0


def test_ibkr_falls_back_after_all_retries_fail(
    monkeypatch,
):
    """
    Yahoo fallback should remain available when every IBKR
    reconnect attempt fails.
    """

    sleep_calls = []

    monkeypatch.setattr(
        time,
        "sleep",
        lambda seconds: sleep_calls.append(
            seconds
        ),
    )

    class FakeProvider:
        attempts = 0
        disconnects = 0

        def __init__(self, client_id):
            self.client_id = client_id

        def get_quotes(self, symbols):
            FakeProvider.attempts += 1

            raise ConnectionError(
                "IBKR unavailable"
            )

        def disconnect(self):
            FakeProvider.disconnects += 1

    monkeypatch.setattr(
        market_data,
        "IBKRDataProvider",
        FakeProvider,
    )

    monkeypatch.setattr(
        market_data,
        "get_live_quote",
        build_test_quote,
    )

    results = market_data.get_quotes(
        ["RY.TO"]
    )

    assert FakeProvider.attempts == 3
    assert FakeProvider.disconnects == 3
    assert sleep_calls == [2, 2]
    assert results[0]["price"] == 99.0