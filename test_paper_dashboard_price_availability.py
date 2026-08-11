"""
Regression tests for missing live prices in the
paper-trading Trade Control Center.

Missing prices must never silently appear as FLAT.
"""

from types import SimpleNamespace

from paper_trading.dashboard import (
    build_paper_dashboard_text,
    calculate_position_holding_window,
)


class FakePortfolio:
    def __init__(self):
        self.open_positions = [
            {
                "symbol": "TEST.TO",
                "entry_price": 100.00,
                "shares": 10,
                "stop_price": 90.00,
                "target_price": 125.00,
            }
        ]

        self.closed_trades = []

    def summary(self, current_prices=None):
        current_prices = (
            current_prices or {}
        )

        current_price = (
            current_prices.get(
                "TEST.TO",
                100.00,
            )
        )

        return {
            "starting_cash": 500000.0,
            "cash": 499000.0,
            "open_position_value": 1000.0,
            "portfolio_exposure": 0.2,
            "portfolio_value": (
                499000.0
                + (10 * current_price)
            ),
            "total_return": 0.0,
            "open_positions": 1,
            "closed_trades": 0,
        }


def build_engine():
    return SimpleNamespace(
        portfolio=FakePortfolio()
    )


def test_missing_price_is_not_reported_as_flat():
    text = build_paper_dashboard_text(
        build_engine(),
        {},
    )

    assert (
        "Status: PRICE UNAVAILABLE"
        in text
    )

    assert (
        "Price Unavailable"
        in text
    )

    assert (
        "Status: FLAT"
        not in text
    )


def test_available_price_still_calculates_profit():
    text = build_paper_dashboard_text(
        build_engine(),
        {
            "TEST.TO": 110.00,
        },
    )

    assert (
        "Status: PROFIT"
        in text
    )

    assert (
        "Current $110.00"
        in text
    )

    assert (
        "P/L $+100.00"
        in text
    )



def test_holding_window_skips_weekends_and_tsx_holidays():
    position = {
        "entry_date": "2026-07-31",
        "max_hold_days": 10,
    }

    result = calculate_position_holding_window(
        position,
        current_date="2026-08-04",
    )

    assert result["trading_days_held"] == 2
    assert result["trading_days_remaining"] == 8
    assert result["time_exit_due"] is False


def test_holding_window_marks_day_10_as_due():
    position = {
        "entry_date": "2026-07-29",
        "max_hold_days": 10,
    }

    result = calculate_position_holding_window(
        position,
        current_date="2026-08-12",
    )

    assert result["trading_days_held"] == 10
    assert result["trading_days_remaining"] == 0
    assert result["time_exit_due"] is True


def test_dashboard_displays_holding_countdown():
    engine = build_engine()

    engine.portfolio.open_positions[0][
        "entry_date"
    ] = "2026-08-07"

    engine.portfolio.open_positions[0][
        "max_hold_days"
    ] = 10

    text = build_paper_dashboard_text(
        engine,
        {
            "TEST.TO": 110.00,
        },
        current_date="2026-08-11",
    )

    assert (
        "Holding Period: Day 3 of 10"
        in text
    )

    assert (
        "Trading Days Remaining: 7"
        in text
    )


def test_missing_price_still_displays_holding_countdown():
    engine = build_engine()

    engine.portfolio.open_positions[0][
        "entry_date"
    ] = "2026-08-07"

    engine.portfolio.open_positions[0][
        "max_hold_days"
    ] = 10

    text = build_paper_dashboard_text(
        engine,
        {},
        current_date="2026-08-11",
    )

    assert (
        "Status: PRICE UNAVAILABLE"
        in text
    )

    assert (
        "Holding Period: Day 3 of 10"
        in text
    )

    assert (
        "Trading Days Remaining: 7"
        in text
    )
