"""
Northstar Quant
Sector-strength research enrichment.

Measures the 20-trading-day performance of a stock's assigned sector
benchmark relative to the broad Canadian market benchmark, XIC.TO.

This module is research-only. It does not change trading decisions.
"""

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)

from research.sector_map import get_sector_mapping


DEFAULT_MARKET_BENCHMARK = "XIC.TO"
DEFAULT_LOOKBACK_DAYS = 20
DOWNLOAD_CALENDAR_DAYS = 120

OUTPERFORMING_THRESHOLD = 1.0
UNDERPERFORMING_THRESHOLD = -1.0


def unavailable_result(
    symbol,
    measurement_date,
    reason,
    sector="",
    sector_etf="",
    data_source="UNAVAILABLE",
):
    """
    Return a consistent unavailable result.
    """

    return {
        "symbol": symbol,
        "sector": sector,
        "sector_etf": sector_etf,
        "market_benchmark": DEFAULT_MARKET_BENCHMARK,
        "sector_return_20": None,
        "market_return_20": None,
        "sector_strength_20": None,
        "sector_status": "UNAVAILABLE",
        "sector_measurement_date": measurement_date,
        "sector_strength_status": "UNAVAILABLE",
        "measurement_date": measurement_date,
        "status": "UNAVAILABLE",
        "reason": reason,
        "data_source": data_source,
    }


def normalize_close_series(history):
    """
    Extract a clean closing-price Series from a yfinance result.

    Handles both standard and MultiIndex DataFrames.
    """
    if history is None or history.empty:
        return pd.Series(dtype="float64")

    if isinstance(history.columns, pd.MultiIndex):
        if "Close" not in history.columns.get_level_values(0):
            return pd.Series(dtype="float64")

        close_data = history["Close"]

        if isinstance(close_data, pd.DataFrame):
            if close_data.empty:
                return pd.Series(dtype="float64")

            close_series = close_data.iloc[:, 0]
        else:
            close_series = close_data
    else:
        if "Close" not in history.columns:
            return pd.Series(dtype="float64")

        close_series = history["Close"]

    return pd.to_numeric(
        close_series,
        errors="coerce",
    ).dropna()


def calculate_return(close_series, lookback_days):
    """
    Calculate percentage return over a trading-day lookback.

    Uses the most recent close and the close from lookback_days
    trading sessions earlier.
    """
    required_rows = lookback_days + 1

    if len(close_series) < required_rows:
        return None

    starting_close = float(close_series.iloc[-required_rows])
    ending_close = float(close_series.iloc[-1])

    if starting_close <= 0:
        return None

    return ((ending_close / starting_close) - 1.0) * 100.0


def classify_sector_strength(sector_strength):
    """
    Classify sector performance relative to XIC.TO.
    """
    if sector_strength >= OUTPERFORMING_THRESHOLD:
        return "OUTPERFORMING"

    if sector_strength <= UNDERPERFORMING_THRESHOLD:
        return "UNDERPERFORMING"

    return "NEUTRAL"


def calculate_sector_strength(
    symbol,
    measurement_date=None,
    lookback_days=DEFAULT_LOOKBACK_DAYS,
):
    """
    Calculate sector strength relative to XIC.

    IBKR ADJUSTED_LAST history is primary because this
    calculation compares historical returns.

    Yahoo Finance remains fallback only.

    This function is research-only and does not alter
    strategy decisions.
    """

    normalized_symbol = str(
        symbol
    ).strip().upper()

    if not normalized_symbol:
        return unavailable_result(
            symbol="",
            measurement_date=measurement_date,
            reason="Symbol is missing.",
        )

    sector_mapping = get_sector_mapping(
        normalized_symbol
    )

    if sector_mapping is None:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=measurement_date,
            reason=(
                "No sector mapping exists "
                "for this symbol."
            ),
        )

    sector, sector_etf = (
        sector_mapping
    )

    if measurement_date is None:
        measurement_datetime = (
            datetime.now()
        )

        normalized_measurement_date = (
            measurement_datetime.strftime(
                "%Y-%m-%d"
            )
        )

    else:
        normalized_measurement_date = str(
            measurement_date
        )

        try:
            measurement_datetime = (
                datetime.strptime(
                    normalized_measurement_date,
                    "%Y-%m-%d",
                )
            )

        except ValueError:
            return unavailable_result(
                symbol=normalized_symbol,
                measurement_date=(
                    normalized_measurement_date
                ),
                reason=(
                    "Measurement date must use "
                    "YYYY-MM-DD format."
                ),
                sector=sector,
                sector_etf=sector_etf,
            )

    if lookback_days < 1:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "Lookback days must be "
                "at least 1."
            ),
            sector=sector,
            sector_etf=sector_etf,
        )

    ibkr_error = ""

    try:
        sector_history = (
            load_ibkr_daily_history(
                symbol=sector_etf,
                measurement_date=(
                    normalized_measurement_date
                ),
                duration="1 Y",
                adjusted=True,
                client_id=22,
            )
        )

        market_history = (
            load_ibkr_daily_history(
                symbol=DEFAULT_MARKET_BENCHMARK,
                measurement_date=(
                    normalized_measurement_date
                ),
                duration="1 Y",
                adjusted=True,
                client_id=23,
            )
        )

        sector_closes = pd.to_numeric(
            sector_history["close"],
            errors="coerce",
        ).dropna()

        market_closes = pd.to_numeric(
            market_history["close"],
            errors="coerce",
        ).dropna()

        sector_return = (
            calculate_return(
                sector_closes,
                lookback_days,
            )
        )

        market_return = (
            calculate_return(
                market_closes,
                lookback_days,
            )
        )

        if (
            sector_return is None
            or market_return is None
        ):
            raise ValueError(
                "Insufficient IBKR return history."
            )

        data_source = (
            "IBKR_ADJUSTED_LAST"
        )

    except Exception as error:
        ibkr_error = str(
            error
        )

        start_date = (
            measurement_datetime
            - timedelta(
                days=DOWNLOAD_CALENDAR_DAYS
            )
        )

        end_date = (
            measurement_datetime
            + timedelta(days=1)
        )

        try:
            history = yf.download(
                tickers=[
                    sector_etf,
                    DEFAULT_MARKET_BENCHMARK,
                ],
                start=start_date.strftime(
                    "%Y-%m-%d"
                ),
                end=end_date.strftime(
                    "%Y-%m-%d"
                ),
                auto_adjust=False,
                progress=False,
                group_by="ticker",
                threads=False,
            )

            if (
                history is None
                or history.empty
            ):
                raise ValueError(
                    "No Yahoo market data returned."
                )

            sector_yahoo = history[
                sector_etf
            ]

            market_yahoo = history[
                DEFAULT_MARKET_BENCHMARK
            ]

            sector_closes = (
                normalize_close_series(
                    sector_yahoo
                )
            )

            market_closes = (
                normalize_close_series(
                    market_yahoo
                )
            )

            sector_return = (
                calculate_return(
                    sector_closes,
                    lookback_days,
                )
            )

            market_return = (
                calculate_return(
                    market_closes,
                    lookback_days,
                )
            )

            if (
                sector_return is None
                or market_return is None
            ):
                raise ValueError(
                    "Insufficient Yahoo "
                    "benchmark history."
                )

            data_source = (
                "YAHOO_FALLBACK"
            )

        except Exception as fallback_error:
            return unavailable_result(
                symbol=normalized_symbol,
                measurement_date=(
                    normalized_measurement_date
                ),
                reason=(
                    "IBKR unavailable: "
                    f"{ibkr_error}; "
                    "Yahoo fallback failed: "
                    f"{fallback_error}"
                ),
                sector=sector,
                sector_etf=sector_etf,
            )

    sector_strength = (
        sector_return
        - market_return
    )

    sector_status = (
        classify_sector_strength(
            sector_strength
        )
    )

    return {
        "symbol": normalized_symbol,
        "sector": sector,
        "sector_etf": sector_etf,
        "market_benchmark": (
            DEFAULT_MARKET_BENCHMARK
        ),
        "sector_return_20": round(
            sector_return,
            4,
        ),
        "market_return_20": round(
            market_return,
            4,
        ),
        "sector_strength_20": round(
            sector_strength,
            4,
        ),
        "sector_status": (
            sector_status
        ),
        "sector_measurement_date": (
            normalized_measurement_date
        ),
        "sector_strength_status": (
            "AVAILABLE"
        ),
        "measurement_date": (
            normalized_measurement_date
        ),
        "status": "AVAILABLE",
        "reason": "",
        "data_source": data_source,
    }


if __name__ == "__main__":
    result = calculate_sector_strength(
        symbol="CNR.TO",
        measurement_date="2026-07-17",
    )

    print(result)