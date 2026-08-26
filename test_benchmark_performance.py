from datetime import date

from mobile_dashboard.benchmark_performance import (
    build_matched_xic_performance,
    calculate_matched_performance,
)


def fake_snapshot():
    return {
        "benchmark": "XIC.TO",
        "history": [
            {
                "date": date(2026, 7, 14),
                "close": 40.00,
            },
            {
                "date": date(2026, 7, 15),
                "close": 40.40,
            },
            {
                "date": date(2026, 7, 16),
                "close": 40.80,
            },
        ],
        "current_price": 41.00,
        "current_price_source": "LAST",
        "history_through": "2026-07-16",
        "data_source": "IBKR_ADJUSTED_LAST",
        "live_source": "IBKR",
        "cache_status": "MISS",
    }


def test_closed_trade_matched_benchmark():
    closed = [
        {
            "entry_date": "2026-07-14",
            "exit_date": "2026-07-16",
            "entry_price": 100.0,
            "shares": 10,
            "profit_loss": 100.0,
        }
    ]

    result = calculate_matched_performance(
        [],
        closed,
        {},
        fake_snapshot(),
    )

    assert result["status"] == "AVAILABLE"
    assert result["cumulative_capital"] == 1000.0
    assert round(
        result["strategy_return"],
        2,
    ) == 10.00

    assert round(
        result["benchmark_return"],
        2,
    ) == 2.00

    assert round(
        result["versus_benchmark"],
        2,
    ) == 8.00


def test_open_trade_uses_current_prices():
    opened = [
        {
            "symbol": "ABC.TO",
            "entry_date": "2026-07-14",
            "entry_price": 100.0,
            "shares": 10,
        }
    ]

    result = calculate_matched_performance(
        opened,
        [],
        {
            "ABC.TO": 105.0,
        },
        fake_snapshot(),
    )

    assert round(
        result["strategy_return"],
        2,
    ) == 5.00

    assert round(
        result["benchmark_return"],
        2,
    ) == 2.50

    assert round(
        result["versus_benchmark"],
        2,
    ) == 2.50


def test_no_trades_does_not_request_data():
    called = {
        "value": False
    }

    def loader(
        start_date,
        end_date,
    ):
        called["value"] = True
        raise AssertionError(
            "Loader should not run."
        )

    result = build_matched_xic_performance(
        [],
        [],
        {},
        snapshot_loader=loader,
    )

    assert result["status"] == "AVAILABLE"
    assert result["trades_evaluated"] == 0
    assert called["value"] is False


def test_loader_failure_fails_closed():
    opened = [
        {
            "symbol": "ABC.TO",
            "entry_date": "2026-07-14",
            "entry_price": 100.0,
            "shares": 10,
        }
    ]

    def loader(
        start_date,
        end_date,
    ):
        raise RuntimeError(
            "benchmark unavailable"
        )

    result = build_matched_xic_performance(
        opened,
        [],
        {
            "ABC.TO": 101.0,
        },
        snapshot_loader=loader,
    )

    assert result["status"] == "UNAVAILABLE"
    assert (
        "benchmark unavailable"
        in result["reason"]
    )
