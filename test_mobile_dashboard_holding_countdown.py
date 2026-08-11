import mobile_dashboard.app as dashboard_module


def make_portfolio(
    symbol,
    strategy,
):
    return {
        "summary": {
            "starting_cash": 500000.0,
            "cash": 499000.0,
            "open_position_value": 1000.0,
            "portfolio_exposure": 0.2,
            "portfolio_value": 500000.0,
            "total_return": 0.0,
            "open_positions": 1,
            "closed_trades": 0,
        },
        "open_positions": [
            {
                "symbol": symbol,
                "strategy": strategy,
                "entry_date": "2026-08-07",
                "entry_price": 100.0,
                "shares": 10,
                "stop_price": 90.0,
                "target_price": 120.0,
                "max_hold_days": 10,
            }
        ],
        "closed_trades": [],
    }


def test_mobile_dashboard_displays_holding_countdown_for_all_strategies(
    monkeypatch,
):
    monkeypatch.setattr(
        dashboard_module,
        "load_latest_prices",
        lambda: {
            "generated_at": "TEST",
            "prices": {
                "MOM.TO": 105.0,
                "BRK.TO": 106.0,
                "MR.TO": 107.0,
            },
        },
    )

    def fake_load_portfolio_data(
        *args,
        **kwargs,
    ):
        state_file = kwargs.get(
            "state_file",
            dashboard_module.PORTFOLIO_STATE_FILE,
        )

        if (
            state_file
            == dashboard_module.BREAKOUT_52WEEK_PORTFOLIO_STATE_FILE
        ):
            return make_portfolio(
                "BRK.TO",
                "52_WEEK_BREAKOUT",
            )

        if (
            state_file
            == dashboard_module.MEAN_REVERSION_PORTFOLIO_STATE_FILE
        ):
            return make_portfolio(
                "MR.TO",
                "MEAN_REVERSION",
            )

        return make_portfolio(
            "MOM.TO",
            "MOMENTUM",
        )

    monkeypatch.setattr(
        dashboard_module,
        "load_portfolio_data",
        fake_load_portfolio_data,
    )

    holding_results = {
        "MOM.TO": {
            "available": True,
            "trading_days_held": 3,
            "max_hold_days": 10,
            "trading_days_remaining": 7,
            "time_exit_due": False,
        },
        "BRK.TO": {
            "available": True,
            "trading_days_held": 5,
            "max_hold_days": 10,
            "trading_days_remaining": 5,
            "time_exit_due": False,
        },
        "MR.TO": {
            "available": True,
            "trading_days_held": 9,
            "max_hold_days": 10,
            "trading_days_remaining": 1,
            "time_exit_due": False,
        },
    }

    monkeypatch.setattr(
        dashboard_module,
        "calculate_position_holding_window",
        lambda position: holding_results[
            position["symbol"]
        ],
    )

    monkeypatch.setattr(
        dashboard_module,
        "file_status",
        lambda file_path: {
            "status": "PASS",
            "text": "AVAILABLE",
        },
    )

    monkeypatch.setattr(
        dashboard_module,
        "count_pending_trades",
        lambda file_path: 0,
    )

    monkeypatch.setattr(
        dashboard_module,
        "load_latest_validation_report",
        lambda: None,
    )

    monkeypatch.setattr(
        dashboard_module,
        "get_tsx_market_status",
        lambda: {
            "status": "CLOSED",
            "is_open": False,
        },
    )

    def fake_load_json_file(
        file_path,
    ):
        if (
            file_path
            == dashboard_module.SCANNER_HEALTH_FILE
        ):
            return {
                "worker": "SCANNER",
                "last_successful_refresh": "--",
                "refresh_id": "TEST",
                "heartbeat": "",
            }

        if (
            file_path
            == dashboard_module.AUTOMATIC_EOD_STATE_FILE
        ):
            return {
                "last_run_date": "--",
            }

        return {}

    monkeypatch.setattr(
        dashboard_module,
        "load_json_file",
        fake_load_json_file,
    )

    html = dashboard_module.dashboard()

    assert html.count(
        "<th>Holding</th>"
    ) == 3

    assert html.count(
        "<th>Days Left</th>"
    ) == 3

    assert "3 / 10" in html
    assert "5 / 10" in html
    assert "9 / 10" in html

    assert "MOM.TO" in html
    assert "BRK.TO" in html
    assert "MR.TO" in html
