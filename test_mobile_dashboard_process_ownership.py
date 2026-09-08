import gui.trading_workstation as workstation_module


def make_workstation():
    workstation = (
        workstation_module
        .TradingWorkstation
        .__new__(
            workstation_module.TradingWorkstation
        )
    )

    workstation.mobile_dashboard_process = None
    workstation.mobile_dashboard_started_here = False

    return workstation


def test_stale_northstar_dashboard_is_recycled(
    monkeypatch,
):
    workstation = make_workstation()

    terminated = []
    saved_pids = []
    cleared_pids = []

    class FakeProcess:
        pid = 4444

        def poll(self):
            return None

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_port_owner",
        lambda: 19792,
    )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_health",
        lambda: {
            "status": "OK",
            "service": "NORTHSTAR_MOBILE_DASHBOARD",
            "pid": 19792,
            "build": "old-build",
        },
    )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_build_id",
        lambda: "new-build",
    )

    monkeypatch.setattr(
        workstation,
        "_terminate_mobile_dashboard_pid",
        lambda pid: (
            terminated.append(pid)
            or True
        ),
    )

    monkeypatch.setattr(
        workstation,
        "_clear_mobile_dashboard_pid",
        lambda expected_pid=None: (
            cleared_pids.append(expected_pid)
        ),
    )

    monkeypatch.setattr(
        workstation,
        "_write_mobile_dashboard_pid",
        lambda pid: saved_pids.append(pid),
    )

    monkeypatch.setattr(
        workstation_module.subprocess,
        "Popen",
        lambda *args, **kwargs: FakeProcess(),
    )

    workstation.start_mobile_dashboard()

    assert terminated == [19792]
    assert cleared_pids == [19792]
    assert saved_pids == [4444]

    assert (
        workstation.mobile_dashboard_process.pid
        == 4444
    )

    assert (
        workstation.mobile_dashboard_started_here
        is True
    )


def test_unrelated_process_on_port_5000_is_never_killed(
    monkeypatch,
):
    workstation = make_workstation()

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_port_owner",
        lambda: 8888,
    )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_health",
        lambda: {
            "status": "OK",
            "service": "SOMETHING_ELSE",
            "pid": 8888,
            "build": "whatever",
        },
    )

    def forbidden_terminate(pid):
        raise AssertionError(
            "Unrelated process must never be killed."
        )

    def forbidden_popen(*args, **kwargs):
        raise AssertionError(
            "Dashboard must not start while "
            "unknown process owns port 5000."
        )

    monkeypatch.setattr(
        workstation,
        "_terminate_mobile_dashboard_pid",
        forbidden_terminate,
    )

    monkeypatch.setattr(
        workstation_module.subprocess,
        "Popen",
        forbidden_popen,
    )

    workstation.start_mobile_dashboard()

    assert workstation.mobile_dashboard_process is None
    assert (
        workstation.mobile_dashboard_started_here
        is False
    )


def test_current_build_dashboard_is_left_running(
    monkeypatch,
):
    workstation = make_workstation()

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_port_owner",
        lambda: 5555,
    )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_health",
        lambda: {
            "status": "OK",
            "service": "NORTHSTAR_MOBILE_DASHBOARD",
            "pid": 5555,
            "build": "current-build",
        },
    )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_build_id",
        lambda: "current-build",
    )

    def forbidden_terminate(pid):
        raise AssertionError(
            "Current dashboard must not be killed."
        )

    def forbidden_popen(*args, **kwargs):
        raise AssertionError(
            "Second dashboard must not be started."
        )

    monkeypatch.setattr(
        workstation,
        "_terminate_mobile_dashboard_pid",
        forbidden_terminate,
    )

    monkeypatch.setattr(
        workstation_module.subprocess,
        "Popen",
        forbidden_popen,
    )

    workstation.start_mobile_dashboard()

    assert workstation.mobile_dashboard_process is None
    assert (
        workstation.mobile_dashboard_started_here
        is False
    )


def test_current_workstation_dashboard_child_is_left_running(
    monkeypatch,
):
    workstation = make_workstation()

    class ExistingProcess:
        pid = 6666

        def poll(self):
            return None

    existing = ExistingProcess()

    workstation.mobile_dashboard_process = existing
    workstation.mobile_dashboard_started_here = True

    def forbidden_port_check():
        raise AssertionError(
            "Port should not be checked when "
            "current dashboard child is alive."
        )

    monkeypatch.setattr(
        workstation,
        "_get_mobile_dashboard_port_owner",
        forbidden_port_check,
    )

    workstation.start_mobile_dashboard()

    assert workstation.mobile_dashboard_process is existing
    assert (
        workstation.mobile_dashboard_started_here
        is True
    )
