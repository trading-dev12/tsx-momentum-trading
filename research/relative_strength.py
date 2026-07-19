"""
Northstar Quant
Relative Strength Research Module

Calculates a stock's 20-trading-day performance relative to
the XIC and XIU Canadian market benchmarks.
"""

from datetime import date, datetime
from pathlib import Path

import pandas as pd


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

    Relative strength is defined as:

        stock return - benchmark return

    The calculation uses adjusted closing prices and only includes
    data available on or before measurement_date.
    """

    result = {
        "measurement_date": _format_date(measurement_date),
        "lookback_days": lookback_days,
        "stock_return_20": None,
        "xic_return_20": None,
        "xiu_return_20": None,
        "rs_xic_20": None,
        "rs_xiu_20": None,
        "status": "UNAVAILABLE",
        "reason": "",
    }

    try:
        stock_prices = load_adjusted_close_history(
            symbol,
            measurement_date,
        )

        xic_prices = load_adjusted_close_history(
            XIC_SYMBOL,
            measurement_date,
        )

        xiu_prices = load_adjusted_close_history(
            XIU_SYMBOL,
            measurement_date,
        )

        stock_return = calculate_period_return(
            stock_prices,
            lookback_days,
        )

        xic_return = calculate_period_return(
            xic_prices,
            lookback_days,
        )

        xiu_return = calculate_period_return(
            xiu_prices,
            lookback_days,
        )

        result["stock_return_20"] = round(stock_return, 4)
        result["xic_return_20"] = round(xic_return, 4)
        result["xiu_return_20"] = round(xiu_return, 4)

        result["rs_xic_20"] = round(
            stock_return - xic_return,
            4,
        )

        result["rs_xiu_20"] = round(
            stock_return - xiu_return,
            4,
        )

        result["status"] = "AVAILABLE"

        return result

    except (FileNotFoundError, ValueError, KeyError) as error:
        result["reason"] = str(error)
        return result

    except Exception as error:
        result["reason"] = (
            "Unexpected relative-strength error: "
            f"{type(error).__name__}: {error}"
        )
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

    return prices.sort_index()


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