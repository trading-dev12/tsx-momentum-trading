import mobile_dashboard.app as dashboard_module


def make_empty_portfolio():
    """
    Return predictable empty portfolio data for dashboard tests.
    """

    return {
        "summary": {
            "starting_cash": 10000.0,
            "cash": 10000.0,
            "open_position_value": 0.0,
            "portfolio_exposure": 0.0,
            "portfolio_value": 10000.0,
            "total_return": 0.0,
            "open_positions": 0,
            "closed_trades": 0,
        },
        "open_positions": [],
        "closed_trades": [],
    }


def test_dashboard_handles_missing_scanner_heartbeat(
    monkeypatch,
):
    """
    A scanner health file without a heartbeat must not
    crash the mobile dashboard.
    """

    monkeypatch.setattr(
        dashboard_module,
        "load_latest_prices",
        lambda: {
            "generated_at": "TEST",
            "prices": {},
        },
    )

    monkeypatch.setattr(
        dashboard_module,
        "load_portfolio_data",
        lambda *args, **kwargs: make_empty_portfolio(),
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
            "status": "OPEN",
            "is_open": True,
        },
    )

    def fake_load_json_file(file_path):
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

    assert isinstance(html, str)
    assert "OFFLINE" in html