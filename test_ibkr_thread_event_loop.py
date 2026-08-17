import asyncio
import threading

import core.ibkr_data_provider as ibkr_module


def test_ibkr_provider_connects_from_worker_thread(monkeypatch):
    observed = {}
    errors = []

    class FakeIB:
        def __init__(self):
            self.connected = False

        def isConnected(self):
            return self.connected

        def connect(
            self,
            host,
            port,
            clientId,
            readonly,
            timeout,
        ):
            loop = asyncio.get_event_loop()

            observed["loop_available"] = loop is not None
            observed["loop_closed"] = loop.is_closed()

            self.connected = True

        def disconnect(self):
            self.connected = False

    monkeypatch.setattr(
        ibkr_module,
        "IB",
        FakeIB,
    )

    def worker():
        asyncio.set_event_loop(None)

        provider = ibkr_module.IBKRDataProvider(
            client_id=99,
        )

        try:
            provider.connect()
        except Exception as error:
            errors.append(error)
        finally:
            provider.disconnect()

    thread = threading.Thread(
        target=worker,
        name="ibkr-regression-worker",
    )

    thread.start()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert not errors, str(errors)
    assert observed["loop_available"] is True
    assert observed["loop_closed"] is False
