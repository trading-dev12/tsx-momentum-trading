"""
Northstar Quant
Volatility Regime Research Module

Measures a stock's volatility environment using only market data
available through the signal date.

This module is research-only. It does not change trading decisions.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


ATR_PERIOD = 14
REALIZED_VOLATILITY_PERIOD = 20
PERCENTILE_LOOKBACK = 252
DOWNLOAD_CALENDAR_DAYS = 500

LOW_PERCENTILE_THRESHOLD = 25.0
HIGH_PERCENTILE_THRESHOLD = 75.0
EXTREME_PERCENTILE_THRESHOLD = 90.0


def unavailable_result(
    symbol,
    measurement_date,
    reason,
):
    """
    Return a consistent unavailable result.
    """
    return {
        "symbol": symbol,
        "close": None,
        "atr_14": None,
        "atr_percent": None,
        "realized_volatility_20": None,
        "volatility_percentile_252": None,
        "volatility_regime": "UNAVAILABLE",
        "measurement_date": measurement_date,
        "status": "UNAVAILABLE",
        "reason": reason,
    }


def normalize_history(history):
    """
    Extract a clean OHLC DataFrame from a yfinance result.

    Handles regular and MultiIndex DataFrames.
    """
    if history is None or history.empty:
        return pd.DataFrame()

    normalized = history.copy()

    if isinstance(normalized.columns, pd.MultiIndex):
        required_fields = {
            "Open",
            "High",
            "Low",
            "Close",
        }

        level_zero = set(
            normalized.columns.get_level_values(0)
        )

        level_one = set(
            normalized.columns.get_level_values(1)
        )

        if required_fields.issubset(level_zero):
            normalized = normalized.droplevel(
                1,
                axis=1,
            )
        elif required_fields.issubset(level_one):
            normalized = normalized.droplevel(
                0,
                axis=1,
            )
        else:
            return pd.DataFrame()

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    if not all(
        column in normalized.columns
        for column in required_columns
    ):
        return pd.DataFrame()

    normalized = normalized[
        required_columns
    ].copy()

    for column in required_columns:
        normalized[column] = pd.to_numeric(
            normalized[column],
            errors="coerce",
        )

    normalized = normalized.dropna(
        subset=required_columns,
    )

    if normalized.empty:
        return pd.DataFrame()

    normalized.index = pd.to_datetime(
        normalized.index,
        errors="coerce",
    )

    normalized = normalized[
        ~normalized.index.isna()
    ]

    return normalized.sort_index()


def calculate_true_range(history):
    """
    Calculate the daily True Range series.
    """
    previous_close = history["Close"].shift(1)

    high_low = (
        history["High"] - history["Low"]
    )

    high_previous_close = (
        history["High"] - previous_close
    ).abs()

    low_previous_close = (
        history["Low"] - previous_close
    ).abs()

    true_range = pd.concat(
        [
            high_low,
            high_previous_close,
            low_previous_close,
        ],
        axis=1,
    ).max(axis=1)

    return true_range


def calculate_realized_volatility(
    close_series,
    period=REALIZED_VOLATILITY_PERIOD,
):
    """
    Calculate annualized rolling realized volatility.

    Uses daily logarithmic returns and a 252-session
    annualization factor.
    """
    log_returns = np.log(
        close_series / close_series.shift(1)
    )

    realized_volatility = (
        log_returns
        .rolling(period)
        .std(ddof=1)
        * np.sqrt(252)
        * 100
    )

    return realized_volatility


def calculate_percentile_rank(
    historical_values,
    current_value,
):
    """
    Calculate the percentile rank of the current value.

    Returns the percentage of historical observations less than
    or equal to the current observation.
    """
    clean_values = pd.to_numeric(
        historical_values,
        errors="coerce",
    ).dropna()

    if clean_values.empty:
        return None

    count_less_or_equal = (
        clean_values <= current_value
    ).sum()

    return (
        count_less_or_equal / len(clean_values)
    ) * 100.0


def classify_volatility_regime(
    volatility_percentile,
):
    """
    Classify volatility using its historical percentile.
    """
    if (
        volatility_percentile
        >= EXTREME_PERCENTILE_THRESHOLD
    ):
        return "EXTREME"

    if (
        volatility_percentile
        >= HIGH_PERCENTILE_THRESHOLD
    ):
        return "HIGH"

    if (
        volatility_percentile
        < LOW_PERCENTILE_THRESHOLD
    ):
        return "LOW"

    return "NORMAL"


def calculate_volatility_regime(
    symbol,
    measurement_date=None,
):
    """
    Calculate a stock's volatility regime on the signal date.

    Args:
        symbol:
            TSX symbol, such as "CNR.TO".

        measurement_date:
            Signal date in YYYY-MM-DD format. Only data available
            through this date is used.

    Returns:
        Dictionary containing ATR, ATR percentage, realized
        volatility, historical percentile, regime, status,
        and reason.
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

    if measurement_date is None:
        measurement_datetime = datetime.now()

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
            measurement_datetime = datetime.strptime(
                normalized_measurement_date,
                "%Y-%m-%d",
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
            )

    start_date = measurement_datetime - timedelta(
        days=DOWNLOAD_CALENDAR_DAYS
    )

    # Yahoo Finance treats the end date as exclusive.
    end_date = measurement_datetime + timedelta(
        days=1
    )

    try:
        history = yf.download(
            normalized_symbol,
            start=start_date.strftime(
                "%Y-%m-%d"
            ),
            end=end_date.strftime(
                "%Y-%m-%d"
            ),
            auto_adjust=False,
            progress=False,
            threads=False,
            multi_level_index=False,
        )
    except Exception as error:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                f"Market-data download failed: {error}"
            ),
        )

    normalized_history = normalize_history(
        history
    )

    if normalized_history.empty:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "No usable market data was returned."
            ),
        )

    measurement_timestamp = pd.Timestamp(
        normalized_measurement_date
    )

    normalized_history = normalized_history[
        normalized_history.index.normalize()
        <= measurement_timestamp
    ]

    if normalized_history.empty:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "No market data was available through "
                "the measurement date."
            ),
        )

    required_rows = max(
        ATR_PERIOD + 1,
        PERCENTILE_LOOKBACK
        + REALIZED_VOLATILITY_PERIOD
        + 1,
    )

    if len(normalized_history) < required_rows:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                f"At least {required_rows} trading "
                "sessions are required."
            ),
        )

    true_range = calculate_true_range(
        normalized_history
    )

    atr_series = true_range.rolling(
        ATR_PERIOD
    ).mean()

    realized_volatility_series = (
        calculate_realized_volatility(
            normalized_history["Close"]
        )
    )

    latest_close = float(
        normalized_history["Close"].iloc[-1]
    )

    latest_atr = float(
        atr_series.iloc[-1]
    )

    latest_realized_volatility = float(
        realized_volatility_series.iloc[-1]
    )

    if (
        pd.isna(latest_atr)
        or pd.isna(latest_realized_volatility)
    ):
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "Volatility calculations produced "
                "insufficient values."
            ),
        )

    if latest_close <= 0:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason="Latest close was invalid.",
        )

    atr_percent = (
        latest_atr / latest_close
    ) * 100.0

    percentile_history = (
        realized_volatility_series
        .dropna()
        .tail(PERCENTILE_LOOKBACK)
    )

    if (
        len(percentile_history)
        < PERCENTILE_LOOKBACK
    ):
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "Insufficient realized-volatility "
                "history for percentile calculation."
            ),
        )

    volatility_percentile = (
        calculate_percentile_rank(
            percentile_history,
            latest_realized_volatility,
        )
    )

    if volatility_percentile is None:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "Volatility percentile could not "
                "be calculated."
            ),
        )

    volatility_regime = (
        classify_volatility_regime(
            volatility_percentile
        )
    )

    return {
        "symbol": normalized_symbol,
        "close": round(
            latest_close,
            4,
        ),
        "atr_14": round(
            latest_atr,
            4,
        ),
        "atr_percent": round(
            atr_percent,
            4,
        ),
        "realized_volatility_20": round(
            latest_realized_volatility,
            4,
        ),
        "volatility_percentile_252": round(
            float(volatility_percentile),
            4,
        ),
        "volatility_regime": volatility_regime,
        "measurement_date": (
            normalized_measurement_date
        ),
        "status": "AVAILABLE",
        "reason": "",
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(
        calculate_volatility_regime(
            symbol="CNR.TO",
            measurement_date="2026-07-17",
        )
    )