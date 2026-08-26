from datetime import date

from research.strategy_risk_benchmark import (
    calculate_whole_strategy_metrics,
)


def test_cash_reduces_whole_strategy_risk():
    closed = [
        {
            "symbol": "ABC.TO",
            "entry_date": "2026-07-14",
            "exit_date": "2026-07-16",
            "entry_price": 100.0,
            "exit_price": 110.0,
            "shares": 10,
            "profit_loss": 100.0,
        }
    ]

    stock_history = {
        "ABC.TO": [
            {
                "date": date(
                    2026,
                    7,
                    14,
                ),
                "close": 100.0,
            },
            {
                "date": date(
                    2026,
                    7,
                    15,
                ),
                "close": 95.0,
            },
            {
                "date": date(
                    2026,
                    7,
                    16,
                ),
                "close": 110.0,
            },
        ]
    }

    xic = [
        {
            "date": date(
                2026,
                7,
                14,
            ),
            "close": 40.0,
        },
        {
            "date": date(
                2026,
                7,
                15,
            ),
            "close": 38.0,
        },
        {
            "date": date(
                2026,
                7,
                16,
            ),
            "close": 41.0,
        },
    ]

    result = (
        calculate_whole_strategy_metrics(
            [],
            closed,
            stock_history,
            xic,
        )
    )

    assert result[
        "required_starting_capital"
    ] == 1000.0

    assert round(
        result[
            "strategy_return"
        ],
        2,
    ) == 10.00

    assert round(
        result[
            "xic_return"
        ],
        2,
    ) == 2.50


def test_required_capital_respects_overlap():
    open_positions = [
        {
            "symbol": "ABC.TO",
            "entry_date": "2026-07-14",
            "entry_price": 100.0,
            "shares": 10,
        },
        {
            "symbol": "XYZ.TO",
            "entry_date": "2026-07-15",
            "entry_price": 50.0,
            "shares": 10,
        },
    ]

    histories = {
        "ABC.TO": [
            {
                "date": date(
                    2026,
                    7,
                    14,
                ),
                "close": 100.0,
            },
            {
                "date": date(
                    2026,
                    7,
                    15,
                ),
                "close": 100.0,
            },
        ],
        "XYZ.TO": [
            {
                "date": date(
                    2026,
                    7,
                    15,
                ),
                "close": 50.0,
            },
        ],
    }

    xic = [
        {
            "date": date(
                2026,
                7,
                14,
            ),
            "close": 40.0,
        },
        {
            "date": date(
                2026,
                7,
                15,
            ),
            "close": 40.0,
        },
    ]

    result = (
        calculate_whole_strategy_metrics(
            open_positions,
            [],
            histories,
            xic,
        )
    )

    assert result[
        "required_starting_capital"
    ] == 1500.0

    assert result[
        "peak_capital_deployed"
    ] == 1500.0


def test_same_day_exit_cash_not_reused_for_entry():
    closed = [
        {
            "symbol": "ABC.TO",
            "entry_date": "2026-07-14",
            "exit_date": "2026-07-15",
            "entry_price": 100.0,
            "exit_price": 100.0,
            "shares": 10,
        }
    ]

    opened = [
        {
            "symbol": "XYZ.TO",
            "entry_date": "2026-07-15",
            "entry_price": 50.0,
            "shares": 10,
        }
    ]

    histories = {
        "ABC.TO": [
            {
                "date": date(
                    2026,
                    7,
                    14,
                ),
                "close": 100.0,
            },
            {
                "date": date(
                    2026,
                    7,
                    15,
                ),
                "close": 100.0,
            },
        ],
        "XYZ.TO": [
            {
                "date": date(
                    2026,
                    7,
                    15,
                ),
                "close": 50.0,
            },
        ],
    }

    xic = [
        {
            "date": date(
                2026,
                7,
                14,
            ),
            "close": 40.0,
        },
        {
            "date": date(
                2026,
                7,
                15,
            ),
            "close": 40.0,
        },
    ]

    result = (
        calculate_whole_strategy_metrics(
            opened,
            closed,
            histories,
            xic,
        )
    )

    #
    # $1,000 old trade is still tied up when
    # the $500 morning entry happens.
    #
    assert result[
        "required_starting_capital"
    ] == 1500.0
