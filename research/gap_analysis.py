"""
Northstar Quant
Gap-analysis research enrichment.

Measures a stock's opening gap on the signal date relative to the
previous trading session.

This module is research-only. It does not change trading decisions.
"""

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


DOWNLOAD_CALENDAR_DAYS = 30

FLAT_GAP_THRESHOLD = 0.10
SMALL_GAP_THRESHOLD = 1.00
MEDIUM_GAP_THRESHOLD = 3.00


def unavailable_result(
    symbol,
    measurement_date,
    reason,
    data_source="UNAVAILABLE",
):
    """
    Return a consistent unavailable result.
    """

    return {
        "symbol": symbol,
        "previous_close": None,
        "previous_high": None,
        "previous_low": None,
        "signal_open": None,
        "gap_percent": None,
        "gap_direction": "UNAVAILABLE",
        "gap_bucket": "UNAVAILABLE",
        "open_vs_previous_high_percent": None,
        "open_vs_previous_low_percent": None,
        "gap_measurement_date": measurement_date,
        "gap_analysis_status": "UNAVAILABLE",
        "measurement_date": measurement_date,
        "status": "UNAVAILABLE",
        "reason": reason,
        "data_source": data_source,
    }


def normalize_history(history, symbol):
    """
    Extract a standard OHLC DataFrame from a yfinance result.

    Handles both regular and MultiIndex DataFrames.
    """
    if history is None or history.empty:
        return pd.DataFrame()

    normalized = history.copy()

    if isinstance(normalized.columns, pd.MultiIndex):
        level_zero = normalized.columns.get_level_values(0)
        level_one = normalized.columns.get_level_values(1)

        if symbol in level_zero:
            normalized = normalized[symbol]
        elif symbol in level_one:
            normalized = normalized.xs(
                symbol,
                axis=1,
                level=1,
            )
        elif len(set(level_zero)) == 1:
            normalized.columns = normalized.columns.droplevel(0)
        elif len(set(level_one)) == 1:
            normalized.columns = normalized.columns.droplevel(1)
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

    normalized = normalized[required_columns].copy()

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


def classify_gap_direction(gap_percent):
    """
    Classify the direction of the opening gap.
    """
    if gap_percent > FLAT_GAP_THRESHOLD:
        return "UP"

    if gap_percent < -FLAT_GAP_THRESHOLD:
        return "DOWN"

    return "FLAT"


def classify_gap_bucket(gap_percent):
    """
    Classify the absolute size of the opening gap.
    """
    absolute_gap = abs(gap_percent)

    if absolute_gap <= FLAT_GAP_THRESHOLD:
        return "FLAT"

    if absolute_gap < SMALL_GAP_THRESHOLD:
        return "SMALL"

    if absolute_gap < MEDIUM_GAP_THRESHOLD:
        return "MEDIUM"

    return "LARGE"


def calculate_percent_difference(
    value,
    reference_value,
):
    """
    Calculate the percentage difference from a reference value.
    """
    if reference_value is None or reference_value <= 0:
        return None

    return (
        (value / reference_value) - 1.0
    ) * 100.0


def calculate_gap_analysis(
    symbol,
    measurement_date=None,
):
    """
    Calculate opening-gap context on the signal date.

    IBKR regular traded daily bars are primary.
    Yahoo Finance remains fallback only.

    This is research-only and does not alter
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
            )

    normalized_history = None
    data_source = "UNAVAILABLE"
    ibkr_error = ""

    try:
        ibkr_history = (
            load_ibkr_daily_history(
                symbol=normalized_symbol,
                measurement_date=(
                    normalized_measurement_date
                ),
                duration="3 M",
                adjusted=False,
            )
        )

        if (
            ibkr_history is not None
            and not ibkr_history.empty
        ):
            history = ibkr_history.rename(
                columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            ).copy()

            history = history.set_index(
                "date"
            )

            normalized_history = (
                normalize_history(
                    history,
                    normalized_symbol,
                )
            )

            if not normalized_history.empty:
                data_source = (
                    "IBKR_TRADES"
                )

    except Exception as error:
        ibkr_error = str(
            error
        )
        normalized_history = None

    if (
        normalized_history is None
        or normalized_history.empty
    ):
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
                tickers=normalized_symbol,
                start=start_date.strftime(
                    "%Y-%m-%d"
                ),
                end=end_date.strftime(
                    "%Y-%m-%d"
                ),
                auto_adjust=False,
                progress=False,
                threads=False,
            )

        except Exception as error:
            return unavailable_result(
                symbol=normalized_symbol,
                measurement_date=(
                    normalized_measurement_date
                ),
                reason=(
                    "IBKR unavailable: "
                    f"{ibkr_error}; "
                    "Yahoo fallback failed: "
                    f"{error}"
                ),
            )

        normalized_history = (
            normalize_history(
                history,
                normalized_symbol,
            )
        )

        data_source = (
            "YAHOO_FALLBACK"
        )

    if normalized_history.empty:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "No usable market data "
                "was returned."
            ),
            data_source=data_source,
        )

    signal_date = pd.Timestamp(
        normalized_measurement_date
    )

    available_dates = (
        normalized_history
        .index
        .normalize()
    )

    signal_rows = (
        normalized_history[
            available_dates
            == signal_date
        ]
    )

    if signal_rows.empty:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "No trading session exists "
                "for the measurement date."
            ),
            data_source=data_source,
        )

    previous_rows = (
        normalized_history[
            available_dates
            < signal_date
        ]
    )

    if previous_rows.empty:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "No previous trading session "
                "was available."
            ),
            data_source=data_source,
        )

    signal_row = (
        signal_rows.iloc[-1]
    )

    previous_row = (
        previous_rows.iloc[-1]
    )

    previous_close = float(
        previous_row["Close"]
    )

    previous_high = float(
        previous_row["High"]
    )

    previous_low = float(
        previous_row["Low"]
    )

    signal_open = float(
        signal_row["Open"]
    )

    if previous_close <= 0:
        return unavailable_result(
            symbol=normalized_symbol,
            measurement_date=(
                normalized_measurement_date
            ),
            reason=(
                "Previous close was invalid."
            ),
            data_source=data_source,
        )

    gap_percent = (
        calculate_percent_difference(
            signal_open,
            previous_close,
        )
    )

    open_vs_previous_high_percent = (
        calculate_percent_difference(
            signal_open,
            previous_high,
        )
    )

    open_vs_previous_low_percent = (
        calculate_percent_difference(
            signal_open,
            previous_low,
        )
    )

    gap_direction = (
        classify_gap_direction(
            gap_percent
        )
    )

    gap_bucket = (
        classify_gap_bucket(
            gap_percent
        )
    )

    return {
        "symbol": normalized_symbol,
        "previous_close": round(
            previous_close,
            4,
        ),
        "previous_high": round(
            previous_high,
            4,
        ),
        "previous_low": round(
            previous_low,
            4,
        ),
        "signal_open": round(
            signal_open,
            4,
        ),
        "gap_percent": round(
            gap_percent,
            4,
        ),
        "gap_direction": (
            gap_direction
        ),
        "gap_bucket": (
            gap_bucket
        ),
        "open_vs_previous_high_percent": round(
            open_vs_previous_high_percent,
            4,
        ),
        "open_vs_previous_low_percent": round(
            open_vs_previous_low_percent,
            4,
        ),
        "gap_measurement_date": (
            normalized_measurement_date
        ),
        "gap_analysis_status": (
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
    result = calculate_gap_analysis(
        symbol="CNR.TO",
        measurement_date="2026-07-17",
    )

    print(result)