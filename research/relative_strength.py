"""
Northstar Quant
Relative Strength Research Module

Calculates a stock's 20-trading-day performance relative to
the XIC and XIU Canadian market benchmarks.
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd

from core.market_hours import (
    get_latest_tsx_trading_day_on_or_before,
)
from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


HISTORICAL_DATA_FOLDER = Path("data/historical")

XIC_SYMBOL = "XIC.TO"
XIU_SYMBOL = "XIU.TO"

DEFAULT_LOOKBACK_DAYS = 20


def calculate_relative_strength(
    symbol,
    measurement_date,
    lookback_days=DEFAULT_LOOKBACK_DAYS,
):
    """
    Calculate relative performance as of the supplied date.

    IBKR ADJUSTED_LAST history is primary so stock splits
    and dividends are handled appropriately.

    Local adjusted-close history remains fallback only.

    Relative strength is:

        stock return - benchmark return

    This function is research-only and does not alter
    strategy decisions.
    """

    result = {
        "measurement_date": (
            _format_date(
                measurement_date
            )
        ),
        "lookback_days": (
            lookback_days
        ),
        "stock_return_20": None,
        "xic_return_20": None,
        "xiu_return_20": None,
        "rs_xic_20": None,
        "rs_xiu_20": None,
        "status": "UNAVAILABLE",
        "reason": "",
        "data_source": "UNAVAILABLE",
    }

    ibkr_error = ""

    try:
        stock_history = (
            load_ibkr_daily_history(
                symbol=symbol,
                measurement_date=(
                    measurement_date
                ),
                duration="2 Y",
                adjusted=True,
                client_id=18,
            )
        )

        xic_history = (
            load_ibkr_daily_history(
                symbol=XIC_SYMBOL,
                measurement_date=(
                    measurement_date
                ),
                duration="2 Y",
                adjusted=True,
                client_id=19,
            )
        )

        xiu_history = (
            load_ibkr_daily_history(
                symbol=XIU_SYMBOL,
                measurement_date=(
                    measurement_date
                ),
                duration="2 Y",
                adjusted=True,
                client_id=20,
            )
        )

        stock_prices = pd.to_numeric(
            stock_history["close"],
            errors="coerce",
        ).dropna()

        xic_prices = pd.to_numeric(
            xic_history["close"],
            errors="coerce",
        ).dropna()

        xiu_prices = pd.to_numeric(
            xiu_history["close"],
            errors="coerce",
        ).dropna()

        stock_return = (
            calculate_period_return(
                stock_prices,
                lookback_days,
            )
        )

        xic_return = (
            calculate_period_return(
                xic_prices,
                lookback_days,
            )
        )

        xiu_return = (
            calculate_period_return(
                xiu_prices,
                lookback_days,
            )
        )

        result[
            "data_source"
        ] = "IBKR_ADJUSTED_LAST"

    except Exception as error:
        ibkr_error = str(
            error
        )

        try:
            stock_prices = (
                load_adjusted_close_history(
                    symbol,
                    measurement_date,
                )
            )

            xic_prices = (
                load_adjusted_close_history(
                    XIC_SYMBOL,
                    measurement_date,
                )
            )

            xiu_prices = (
                load_adjusted_close_history(
                    XIU_SYMBOL,
                    measurement_date,
                )
            )

            stock_return = (
                calculate_period_return(
                    stock_prices,
                    lookback_days,
                )
            )

            xic_return = (
                calculate_period_return(
                    xic_prices,
                    lookback_days,
                )
            )

            xiu_return = (
                calculate_period_return(
                    xiu_prices,
                    lookback_days,
                )
            )

            result[
                "data_source"
            ] = "LOCAL_ADJUSTED_FALLBACK"

        except Exception as fallback_error:
            result["reason"] = (
                "IBKR unavailable: "
                f"{ibkr_error}; "
                "local adjusted fallback failed: "
                f"{fallback_error}"
            )

            return result

    result[
        "stock_return_20"
    ] = round(
        stock_return,
        4,
    )

    result[
        "xic_return_20"
    ] = round(
        xic_return,
        4,
    )

    result[
        "xiu_return_20"
    ] = round(
        xiu_return,
        4,
    )

    result[
        "rs_xic_20"
    ] = round(
        stock_return
        - xic_return,
        4,
    )

    result[
        "rs_xiu_20"
    ] = round(
        stock_return
        - xiu_return,
        4,
    )

    result["status"] = (
        "AVAILABLE"
    )

    result["reason"] = ""

    return result


def load_adjusted_close_history(symbol, measurement_date):
    """
    Load adjusted closing prices from a saved yfinance CSV.

    The project's yfinance files contain a three-row header:

        Price,Adj Close,Close,...
        Ticker,SYMBOL,SYMBOL,...
        Date,,,,,
    """

    file_path = historical_file_path(symbol)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Historical data file not found for {symbol}: "
            f"{file_path}"
        )

    data = pd.read_csv(
        file_path,
        header=[0, 1],
        index_col=0,
        parse_dates=True,
    )

    adjusted_close_column = _find_adjusted_close_column(data)

    prices = pd.to_numeric(
        data[adjusted_close_column],
        errors="coerce",
    ).dropna()

    cutoff_date = pd.Timestamp(measurement_date).normalize()

    prices = prices[
        prices.index.normalize() <= cutoff_date
    ]

    if prices.empty:
        raise ValueError(
            f"No historical prices for {symbol} on or before "
            f"{cutoff_date.date()}."
        )

    prices = prices.sort_index()

    expected_date = (
        get_latest_tsx_trading_day_on_or_before(
            cutoff_date.date()
        )
    )

    latest_date = prices.index[-1].date()

    if latest_date != expected_date:
        raise ValueError(
            f"Local historical data for {symbol} is stale: "
            f"expected through {expected_date.isoformat()}, "
            f"latest available is {latest_date.isoformat()}."
        )

    return prices


def calculate_period_return(prices, lookback_days):
    """
    Calculate percentage return across a trading-day lookback.

    A 20-day return requires 21 closing-price observations:
    today's close and the close 20 trading sessions earlier.
    """

    required_rows = lookback_days + 1

    if len(prices) < required_rows:
        raise ValueError(
            f"At least {required_rows} price rows are required "
            f"for a {lookback_days}-day return; found "
            f"{len(prices)}."
        )

    ending_price = float(prices.iloc[-1])
    starting_price = float(
        prices.iloc[-required_rows]
    )

    if starting_price <= 0:
        raise ValueError(
            "Starting price must be greater than zero."
        )

    return (
        (ending_price / starting_price) - 1
    ) * 100


def historical_file_path(symbol):
    """
    Convert a Yahoo symbol to its saved historical CSV path.

    Example:
        SHOP.TO -> data/historical/SHOP_TO.csv
    """

    filename = f"{symbol.replace('.', '_')}.csv"
    return HISTORICAL_DATA_FOLDER / filename


def _find_adjusted_close_column(data):
    for column in data.columns:
        first_level = str(column[0]).strip().lower()

        if first_level == "adj close":
            return column

    raise KeyError(
        "Adjusted Close column was not found in the "
        "historical CSV."
    )


def _format_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return str(value)