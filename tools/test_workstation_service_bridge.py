"""
Safe tests for the Northstar workstation service bridge.

No real execution, EOD, scanner, portfolio, or trading
service is started by these tests.
"""

from unittest.mock import MagicMock, patch

import core.workstation_service_bridge as bridge


def test_gui_starts_local_service_when_it_owns_lock():
    fake_start = MagicMock(
        return_value="LOCAL_THREAD"
    )

    fake_ownership = MagicMock()
    fake_ownership.acquired = True

    with patch.object(
        bridge,
        "GUI_SERVICE_OWNERSHIP",
        fake_ownership,
    ):
        starter = (
            bridge.build_workstation_service_starter(
                fake_start,
                "execution_status",
            )
        )

        result = starter(
            "ENGINE",
            retry_seconds=60,
        )

    assert result == "LOCAL_THREAD"

    fake_start.assert_called_once_with(
        "ENGINE",
        retry_seconds=60,
    )

    fake_ownership.acquire.assert_not_called()


def test_gui_acquires_lock_and_starts_local_service():
    fake_start = MagicMock(
        return_value="LOCAL_THREAD"
    )

    fake_ownership = MagicMock()
    fake_ownership.acquired = False
    fake_ownership.acquire.return_value = True

    with patch.object(
        bridge,
        "GUI_SERVICE_OWNERSHIP",
        fake_ownership,
    ):
        starter = (
            bridge.build_workstation_service_starter(
                fake_start,
                "execution_status",
            )
        )

        result = starter("ENGINE")

    assert result == "LOCAL_THREAD"

    fake_ownership.acquire.assert_called_once_with()

    fake_start.assert_called_once_with(
        "ENGINE"
    )


def test_gui_does_not_start_duplicate_when_headless_owns_lock():
    fake_start = MagicMock()

    fake_ownership = MagicMock()
    fake_ownership.acquired = False
    fake_ownership.acquire.return_value = False

    with patch.object(
        bridge,
        "GUI_SERVICE_OWNERSHIP",
        fake_ownership,
    ):
        starter = (
            bridge.build_workstation_service_starter(
                fake_start,
                "execution_status",
            )
        )

        result = starter("ENGINE")

    assert isinstance(
        result,
        bridge.HeadlessServiceThreadProxy,
    )

    assert result.service_key == (
        "execution_status"
    )

    fake_ownership.acquire.assert_called_once_with()

    fake_start.assert_not_called()


def test_headless_proxy_reports_running_service():
    proxy = bridge.HeadlessServiceThreadProxy(
        "execution_status"
    )

    with patch.object(
        bridge,
        "is_headless_service_running",
        return_value=True,
    ) as status_check:
        assert proxy.is_alive() is True

    status_check.assert_called_once_with(
        "execution_status"
    )


def test_headless_proxy_reports_stopped_service():
    proxy = bridge.HeadlessServiceThreadProxy(
        "execution_status"
    )

    with patch.object(
        bridge,
        "is_headless_service_running",
        return_value=False,
    ) as status_check:
        assert proxy.is_alive() is False

    status_check.assert_called_once_with(
        "execution_status"
    )
