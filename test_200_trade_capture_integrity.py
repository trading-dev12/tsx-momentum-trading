from datetime import date
import json

from research.enrichment_integrity import (
    analyze_200_trade_capture_integrity,
    missing_200_trade_capture_fields,
)


def complete_trade(
    symbol="TEST.TO",
    entry_date="2026-08-18",
):
    return {
        "symbol": symbol,
        "strategy": "MOMENTUM",
        "entry_date": entry_date,

        "signal_date": "2026-08-17",
        "signal_close": "100.0",
        "signal_reason": "Qualified setup",
        "signal_snapshot_json": (
            json.dumps(
                {
                    "symbol": symbol,
                    "decision": "READY",
                    "tmqs": 90,
                    "rvol": 2.0,
                }
            )
        ),

        "entry_context_status": "AVAILABLE",
        "entry_cash_before": "500000",
        "entry_portfolio_value_before": "500000",
        "entry_open_position_value_before": "0",
        "entry_portfolio_exposure_before": "0",
        "entry_open_positions_before": "0",
        "entry_closed_trades_before": "0",
        "entry_position_value": "5000",
        "entry_initial_risk_per_share": "2",
        "entry_initial_risk_amount": "100",
        "entry_risk_model": "fixed",
        "entry_risk_budget": "100",
        "entry_max_position_value": "100000",
        "entry_sizing_limiting_factor": "risk",
        "entry_sizing_decision": "ACCEPTED",
        "entry_atr_multiplier": "2",
        "entry_reward_multiplier": "2.5",
        "entry_max_hold_days": "10",
        "signal_to_entry_gap_percent": "1.0",

        "entry_git_commit": "a" * 40,
        "entry_project_version": "1.0",
        "entry_config_sha256": "b" * 64,
        "entry_strategy_code_sha256": "c" * 64,
        "entry_config_snapshot_json": (
            json.dumps(
                {
                    "config/settings.json": {
                        "version": "1.0",
                    }
                }
            )
        ),
        "entry_fingerprint_status": "AVAILABLE",
        "entry_fingerprint_error": "",

        "entry_quote_status": "AVAILABLE",
        "entry_quote_source": "IBKR",
        "entry_quote_timestamp": (
            "2026-08-18T09:30:05-04:00"
        ),
        "entry_bid": "100.95",
        "entry_ask": "101.05",
        "entry_last": "101.00",
        "entry_midpoint": "101.00",
        "entry_spread_amount": "0.10",
        "entry_spread_percent": "0.099",
        "entry_quote_error": "",

        "exit_quote_status": "AVAILABLE",
        "exit_quote_source": "IBKR",
        "exit_quote_timestamp": (
            "2026-08-20T14:30:00-04:00"
        ),
        "exit_bid": "105.95",
        "exit_ask": "106.05",
        "exit_last": "106.00",
        "exit_midpoint": "106.00",
        "exit_spread_amount": "0.10",
        "exit_spread_percent": "0.094",
        "exit_quote_error": "",

        "trade_path_status": "COMPLETE",
        "trade_path_source": "IBKR_ONE_MINUTE",
        "trade_path_bar_count": "500",
        "trade_path_bars_saved": "500",
        "trade_path_error": "",
        "highest_price": "108",
        "lowest_price": "99",
        "mfe_amount": "350",
        "mfe_percent": "6.93",
        "mfe_r": "3.5",
        "mfe_timestamp": (
            "2026-08-19T11:00:00-04:00"
        ),
        "mae_amount": "100",
        "mae_percent": "1.98",
        "mae_r": "1.0",
        "mae_timestamp": (
            "2026-08-18T10:00:00-04:00"
        ),
    }


def test_complete_new_trade_passes_capture_integrity():
    trade = complete_trade()

    assert (
        missing_200_trade_capture_fields(
            trade
        )
        == {}
    )

    result = (
        analyze_200_trade_capture_integrity(
            [trade]
        )
    )

    assert result["integrity_status"] == "PASS"
    assert result["monitored_trade_count"] == 1
    assert result["complete_capture_count"] == 1
    assert result["incomplete_capture_count"] == 0

    assert (
        result["capture_coverage_percent"]
        == 100.0
    )

    assert (
        result["data_availability_status"]
        == "COMPLETE"
    )


def test_legacy_trade_does_not_fail_new_capture_monitor():
    trade = {
        "symbol": "OLD.TO",
        "entry_date": "2026-08-17",
    }

    result = (
        analyze_200_trade_capture_integrity(
            [trade],
            monitor_start_date=date(
                2026,
                8,
                18,
            ),
        )
    )

    assert result["legacy_trade_count"] == 1
    assert result["monitored_trade_count"] == 0

    assert (
        result["integrity_status"]
        == "NO_MONITORED_TRADES_YET"
    )


def test_missing_signal_snapshot_is_detected():
    trade = complete_trade()

    trade[
        "signal_snapshot_json"
    ] = ""

    result = (
        analyze_200_trade_capture_integrity(
            [trade]
        )
    )

    assert result["integrity_status"] == "FAIL"

    assert (
        result["group_issue_counts"][
            "signal_snapshot"
        ]
        == 1
    )

    assert (
        result["field_issue_counts"][
            "signal_snapshot_json"
        ]
        == 1
    )


def test_explicit_yahoo_quote_unavailable_is_valid_capture():
    trade = complete_trade()

    for prefix in (
        "entry",
        "exit",
    ):
        trade[
            f"{prefix}_quote_status"
        ] = "UNAVAILABLE"

        trade[
            f"{prefix}_quote_source"
        ] = "YAHOO_FALLBACK"

        trade[
            f"{prefix}_bid"
        ] = ""

        trade[
            f"{prefix}_ask"
        ] = ""

        trade[
            f"{prefix}_last"
        ] = ""

        trade[
            f"{prefix}_midpoint"
        ] = ""

        trade[
            f"{prefix}_spread_amount"
        ] = ""

        trade[
            f"{prefix}_spread_percent"
        ] = ""

        trade[
            f"{prefix}_quote_error"
        ] = (
            "Bid/ask snapshot unavailable."
        )

    result = (
        analyze_200_trade_capture_integrity(
            [trade]
        )
    )

    # Capture mechanism worked and explicitly recorded
    # the missing market microstructure observation.
    assert result["integrity_status"] == "PASS"

    # But the preferred research data was unavailable.
    assert (
        result["data_availability_status"]
        == "PARTIAL"
    )

    assert (
        result["entry_quote_status_counts"][
            "UNAVAILABLE"
        ]
        == 1
    )


def test_trade_path_error_is_recorded_not_silently_missing():
    trade = complete_trade()

    trade["trade_path_status"] = "ERROR"
    trade["trade_path_source"] = "IBKR"
    trade["trade_path_bar_count"] = "0"
    trade["trade_path_bars_saved"] = "0"

    trade[
        "trade_path_error"
    ] = "Historical request failed"

    for field in (
        "highest_price",
        "lowest_price",
        "mfe_amount",
        "mfe_percent",
        "mfe_r",
        "mfe_timestamp",
        "mae_amount",
        "mae_percent",
        "mae_r",
        "mae_timestamp",
    ):
        trade[field] = ""

    result = (
        analyze_200_trade_capture_integrity(
            [trade]
        )
    )

    assert result["integrity_status"] == "PASS"

    assert (
        result["data_availability_status"]
        == "PARTIAL"
    )

    assert (
        result["trade_path_status_counts"][
            "ERROR"
        ]
        == 1
    )


def test_invalid_runtime_fingerprint_fails():
    trade = complete_trade()

    trade[
        "entry_strategy_code_sha256"
    ] = "NOT_A_SHA"

    result = (
        analyze_200_trade_capture_integrity(
            [trade]
        )
    )

    assert result["integrity_status"] == "FAIL"

    assert (
        result["group_issue_counts"][
            "entry_fingerprint"
        ]
        == 1
    )

    assert (
        "entry_strategy_code_sha256"
        in result["incomplete_trades"][0][
            "fields"
        ]
    )
