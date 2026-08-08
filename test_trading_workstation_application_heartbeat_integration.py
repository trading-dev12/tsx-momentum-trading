import gui.trading_workstation as workstation_module


class OneCycleStopEvent:
    def __init__(self):
        self.check_count = 0
        self.wait_seconds = []

    def is_set(self):
        self.check_count += 1
        return self.check_count > 1

    def wait(self, seconds):
        self.wait_seconds.append(
            seconds
        )


def test_application_heartbeat_worker_runs_one_cycle(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        workstation_module,
        "record_application_heartbeat",
        lambda: calls.append(
            "heartbeat"
        ),
    )

    monkeypatch.setattr(
        workstation_module,
        "try_send_pending_application_restart_alert",
        lambda: calls.append(
            "restart_alert"
        ),
    )

    stop_event = OneCycleStopEvent()

    workstation_module.application_heartbeat_worker(
        stop_event=stop_event,
        heartbeat_seconds=30,
    )

    assert calls == [
        "heartbeat",
        "restart_alert",
    ]

    assert stop_event.wait_seconds == [
        30
    ]


def test_on_close_records_clean_shutdown_after_worker_stops(
    monkeypatch,
):
    events = []

    class FakeStopEvent:
        def set(self):
            events.append(
                "stop_event"
            )

    class FakeThread:
        def is_alive(self):
            return True

        def join(self, timeout=None):
            events.append(
                f"join:{timeout}"
            )

    class FakeRoot:
        def destroy(self):
            events.append(
                "destroy"
            )

    monkeypatch.setattr(
        workstation_module,
        "record_clean_shutdown",
        lambda: events.append(
            "clean_shutdown"
        ),
    )

    workstation = (
        workstation_module
        .TradingWorkstation
        .__new__(
            workstation_module.TradingWorkstation
        )
    )

    workstation.application_heartbeat_stop_event = (
        FakeStopEvent()
    )

    workstation.application_heartbeat_thread = (
        FakeThread()
    )

    workstation.root = FakeRoot()

    workstation.stop_mobile_dashboard = (
        lambda: events.append(
            "stop_dashboard"
        )
    )

    workstation.on_close()

    assert events == [
        "stop_event",
        "join:2.0",
        "clean_shutdown",
        "stop_dashboard",
        "destroy",
    ]


def test_main_starts_heartbeat_and_queues_restart_alert(
    monkeypatch,
):
    events = []

    startup_result = {
        "transition": "UNEXPECTED_RESTART",
        "previous_last_heartbeat": (
            "2026-08-07T10:00:00-04:00"
        ),
        "downtime_seconds": 900,
    }

    class FakeRoot:
        def mainloop(self):
            events.append(
                "mainloop"
            )

    class FakeWorkstation:
        def __init__(self, root):
            self.root = root

    class FakeEvent:
        pass

    class FakeThread:
        def __init__(
            self,
            target,
            args,
            daemon,
        ):
            self.target = target
            self.args = args
            self.daemon = daemon
            self.started = False

            events.append(
                "thread_created"
            )

        def start(self):
            self.started = True

            events.append(
                "thread_started"
            )

    fake_root = FakeRoot()
    fake_event = FakeEvent()

    created = {}

    monkeypatch.setattr(
        workstation_module,
        "record_application_start",
        lambda: startup_result,
    )

    monkeypatch.setattr(
        workstation_module,
        "queue_application_restart_alert",
        lambda result: events.append(
            (
                "queued",
                result,
            )
        ),
    )

    monkeypatch.setattr(
        workstation_module.tk,
        "Tk",
        lambda: fake_root,
    )

    def fake_workstation_factory(root):
        workstation = FakeWorkstation(
            root
        )

        created["workstation"] = (
            workstation
        )

        return workstation

    monkeypatch.setattr(
        workstation_module,
        "TradingWorkstation",
        fake_workstation_factory,
    )

    monkeypatch.setattr(
        workstation_module.threading,
        "Event",
        lambda: fake_event,
    )

    def fake_thread_factory(
        target,
        args,
        daemon,
    ):
        thread = FakeThread(
            target=target,
            args=args,
            daemon=daemon,
        )

        created["thread"] = thread

        return thread

    monkeypatch.setattr(
        workstation_module.threading,
        "Thread",
        fake_thread_factory,
    )

    workstation_module.main()

    workstation = created[
        "workstation"
    ]

    thread = created[
        "thread"
    ]

    assert events[0] == (
        "queued",
        startup_result,
    )

    assert (
        workstation
        .application_heartbeat_stop_event
        is fake_event
    )

    assert (
        workstation
        .application_heartbeat_thread
        is thread
    )

    assert (
        thread.target
        is workstation_module
        .application_heartbeat_worker
    )

    assert thread.args == (
        fake_event,
    )

    assert thread.daemon is True
    assert thread.started is True

    assert "mainloop" in events