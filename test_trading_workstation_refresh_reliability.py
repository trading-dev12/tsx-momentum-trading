from gui import trading_workstation as workstation_module
from gui.trading_workstation import TradingWorkstation


class FakeWidget:
    def __init__(self):
        self.values = {}

    def config(self, **kwargs):
        self.values.update(kwargs)


class FakeRoot:
    def __init__(self):
        self.scheduled = []

    def after(self, delay, callback):
        self.scheduled.append((delay, callback))


def test_market_open_transition_refreshes_immediately():
    workstation = TradingWorkstation.__new__(
        TradingWorkstation
    )

    refresh_calls = []

    workstation.last_market_open_state = False
    workstation.is_refreshing = False
    workstation.refresh_data = (
        lambda: refresh_calls.append("refresh")
    )

    started = (
        workstation.handle_market_session_transition(
            {"is_open": True}
        )
    )

    assert started is True
    assert refresh_calls == ["refresh"]
    assert workstation.last_market_open_state is True

    started_again = (
        workstation.handle_market_session_transition(
            {"is_open": True}
        )
    )

    assert started_again is False
    assert refresh_calls == ["refresh"]


def test_slow_refresh_warning_does_not_discard_worker():
    workstation = TradingWorkstation.__new__(
        TradingWorkstation
    )

    workstation.is_refreshing = True
    workstation.active_refresh_id = 7
    workstation.refresh_slow_warning_ms = 240_000
    workstation.refresh_slow_warning_active = False
    workstation.status_label = FakeWidget()

    workstation.handle_refresh_slow_warning(7)

    assert workstation.is_refreshing is True
    assert workstation.active_refresh_id == 7
    assert workstation.refresh_slow_warning_active is True
    assert "longer than usual" in (
        workstation.status_label.values["text"]
    )


def test_refresh_schedules_warning_before_hard_timeout(
    monkeypatch,
):
    workstation = TradingWorkstation.__new__(
        TradingWorkstation
    )

    workstation.current_view = "LIVE"
    workstation.is_refreshing = False
    workstation.refresh_sequence = 0
    workstation.active_refresh_id = None
    workstation.refresh_interval_seconds = 300
    workstation.countdown_seconds = 300
    workstation.refresh_slow_warning_ms = 240_000
    workstation.refresh_timeout_ms = 600_000
    workstation.refresh_slow_warning_active = False

    workstation.root = FakeRoot()
    workstation.refresh_button = FakeWidget()
    workstation.status_label = FakeWidget()
    workstation.write_scanner_health = (
        lambda status: None
    )
    workstation.load_data = lambda refresh_id: None

    monkeypatch.setattr(
        workstation_module,
        "is_headless_service_running",
        lambda service_key: False,
    )

    class FakeThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        FakeThread,
    )

    workstation.refresh_data()

    delays = [
        delay
        for delay, callback
        in workstation.root.scheduled
    ]

    assert delays == [240_000, 600_000]
    assert workstation.is_refreshing is True
    assert workstation.active_refresh_id == 1
