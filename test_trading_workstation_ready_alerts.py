from gui import trading_workstation as workstation_module
from gui.trading_workstation import TradingWorkstation


class ImmediateThread:
    def __init__(self, target=None, **kwargs):
        self.target = target

    def start(self):
        if self.target:
            self.target()


def make_ready_quote():
    return {
        "symbol": "CNQ.TO",
        "decision": "READY",
        "price": 68.38,
        "tmqs": 100,
        "confidence_score": 95,
        "relative_volume": 1.87,
        "breakout_status": "BREAKOUT",
        "reason": "All rules passed",
    }


def make_workstation():
    workstation = TradingWorkstation.__new__(
        TradingWorkstation
    )
    workstation.previous_ready_symbols = set()
    workstation.notified_ready_symbols = set()
    return workstation


def test_live_ready_alert_is_clearly_informational(
    monkeypatch,
):
    messages = []

    monkeypatch.setattr(
        workstation_module,
        "get_tsx_market_status",
        lambda: {"is_open": True},
    )

    monkeypatch.setattr(
        workstation_module,
        "send_telegram_message",
        lambda message: (
            messages.append(message)
            or {"success": True}
        ),
    )

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    workstation = make_workstation()

    workstation.check_ready_alerts(
        [make_ready_quote()]
    )

    assert len(messages) == 1

    message = messages[0]

    assert "LIVE READY ALERT" in message
    assert "INFORMATIONAL ONLY - NOT QUEUED" in message
    assert (
        "Official next-day entries are determined "
        "by the EOD scan."
    ) in message


def test_live_ready_alert_is_suppressed_after_market_close(
    monkeypatch,
):
    messages = []

    monkeypatch.setattr(
        workstation_module,
        "get_tsx_market_status",
        lambda: {"is_open": False},
    )

    monkeypatch.setattr(
        workstation_module,
        "send_telegram_message",
        lambda message: (
            messages.append(message)
            or {"success": True}
        ),
    )

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        ImmediateThread,
    )

    workstation = make_workstation()

    workstation.check_ready_alerts(
        [make_ready_quote()]
    )

    assert messages == []
    assert workstation.notified_ready_symbols == set()
