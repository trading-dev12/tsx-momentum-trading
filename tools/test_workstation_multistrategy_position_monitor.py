from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gui.trading_workstation import TradingWorkstation


def make_engine(open_count=1):
    positions = [
        {"symbol": f"TEST{i}.TO"}
        for i in range(open_count)
    ]

    return SimpleNamespace(
        portfolio=SimpleNamespace(
            open_positions=positions
        )
    )


def make_workstation():
    workstation = object.__new__(
        TradingWorkstation
    )

    workstation.paper_engine = make_engine()
    workstation.breakout_52week_engine = (
        make_engine()
    )
    workstation.mean_reversion_engine = (
        make_engine()
    )

    workstation.update_paper_portfolio_panel = (
        MagicMock()
    )

    return workstation


def test_gui_monitor_passes_all_three_strategies():
    workstation = make_workstation()

    with (
        patch(
            "gui.trading_workstation."
            "is_headless_service_running",
            return_value=False,
        ),
        patch(
            "gui.trading_workstation."
            "run_headless_position_monitor_cycle",
            return_value={
                "closed_total": 0,
            },
        ) as monitor,
    ):
        workstation.monitor_paper_positions()

    monitor.assert_called_once()

    engines = monitor.call_args.args[0]

    assert engines == {
        "momentum": workstation.paper_engine,
        "52_week_breakout": (
            workstation.breakout_52week_engine
        ),
        "mean_reversion": (
            workstation.mean_reversion_engine
        ),
    }


def test_gui_monitor_refreshes_panel_after_close():
    workstation = make_workstation()

    with (
        patch(
            "gui.trading_workstation."
            "is_headless_service_running",
            return_value=False,
        ),
        patch(
            "gui.trading_workstation."
            "run_headless_position_monitor_cycle",
            return_value={
                "closed_total": 2,
            },
        ),
    ):
        workstation.monitor_paper_positions()

    workstation.update_paper_portfolio_panel\
        .assert_called_once_with()


def test_gui_monitor_defers_to_headless_owner():
    workstation = make_workstation()

    with (
        patch(
            "gui.trading_workstation."
            "is_headless_service_running",
            return_value=True,
        ),
        patch(
            "gui.trading_workstation."
            "run_headless_position_monitor_cycle",
        ) as monitor,
    ):
        workstation.monitor_paper_positions()

    monitor.assert_not_called()


def test_gui_monitor_skips_when_no_positions():
    workstation = make_workstation()

    workstation.paper_engine = make_engine(0)
    workstation.breakout_52week_engine = (
        make_engine(0)
    )
    workstation.mean_reversion_engine = (
        make_engine(0)
    )

    with (
        patch(
            "gui.trading_workstation."
            "is_headless_service_running",
            return_value=False,
        ),
        patch(
            "gui.trading_workstation."
            "run_headless_position_monitor_cycle",
        ) as monitor,
    ):
        workstation.monitor_paper_positions()

    monitor.assert_not_called()
