"""
Northstar Quant
Moving Average Context Research Module

Measures the technical context of a stock on the signal date.
"""

from datetime import datetime, timedelta

import yfinance as yf

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


def calculate_moving_average_context(
    symbol,
    measurement_date,
):
    """
    Measure moving-average context using only information
    available on the signal date.

    IBKR regular traded daily bars are primary.
    Yahoo Finance is retained only as a fallback.

    This function is research-only and does not alter
    strategy decisions.
    """

    result = {
        "trend_alignment": None,
        "close": None,
        "sma_20": None,
        "sma_50": None,
        "sma_200": None,
        "close_vs_sma20_percent": None,
        "close_vs_sma50_percent": None,
        "close_vs_sma200_percent": None,
        "sma20_vs_sma50_percent": None,
        "sma50_vs_sma200_percent": None,
        "measurement_date": measurement_date,
        "status": "UNAVAILABLE",
        "reason": "",
        "data_source": "UNAVAILABLE",
    }

    history = None
    ibkr_error = ""

    try:
        history = load_ibkr_daily_history(
            symbol=symbol,
            measurement_date=measurement_date,
            duration="2 Y",
            adjusted=False,
        )

        if (
            history is not None
            and len(history) >= 200
        ):
            history = history.rename(
                columns={
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )

            result["data_source"] = (
                "IBKR_TRADES"
            )
        else:
            history = None

    except Exception as error:
        ibkr_error = str(
            error
        )
        history = None

    if history is None:
        try:
            measurement_datetime = (
                datetime.strptime(
                    measurement_date,
                    "%Y-%m-%d",
                )
            )

            start_date = (
                measurement_datetime
                - timedelta(days=400)
            ).strftime(
                "%Y-%m-%d"
            )

            end_date = (
                measurement_datetime
                + timedelta(days=1)
            ).strftime(
                "%Y-%m-%d"
            )

            history = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                progress=False,
                multi_level_index=False,
            )

            if history.empty:
                result["reason"] = (
                    "No historical data. "
                    f"IBKR error: {ibkr_error}"
                )
                return result

            result["data_source"] = (
                "YAHOO_FALLBACK"
            )

        except Exception as error:
            result["reason"] = (
                "IBKR unavailable: "
                f"{ibkr_error}; "
                "Yahoo fallback failed: "
                f"{error}"
            )
            return result

    history = history.tail(
        250
    ).copy()

    if len(history) < 200:
        result["reason"] = (
            "Insufficient history."
        )
        return result

    history["SMA20"] = (
        history["Close"]
        .rolling(20)
        .mean()
    )

    history["SMA50"] = (
        history["Close"]
        .rolling(50)
        .mean()
    )

    history["SMA200"] = (
        history["Close"]
        .rolling(200)
        .mean()
    )

    latest = history.iloc[-1]

    close = float(
        latest["Close"]
    )

    sma20 = float(
        latest["SMA20"]
    )

    sma50 = float(
        latest["SMA50"]
    )

    sma200 = float(
        latest["SMA200"]
    )

    result["close"] = round(
        close,
        4,
    )

    result["sma_20"] = round(
        sma20,
        4,
    )

    result["sma_50"] = round(
        sma50,
        4,
    )

    result["sma_200"] = round(
        sma200,
        4,
    )

    result[
        "close_vs_sma20_percent"
    ] = round(
        (
            (close - sma20)
            / sma20
        )
        * 100,
        4,
    )

    result[
        "close_vs_sma50_percent"
    ] = round(
        (
            (close - sma50)
            / sma50
        )
        * 100,
        4,
    )

    result[
        "close_vs_sma200_percent"
    ] = round(
        (
            (close - sma200)
            / sma200
        )
        * 100,
        4,
    )

    result[
        "sma20_vs_sma50_percent"
    ] = round(
        (
            (sma20 - sma50)
            / sma50
        )
        * 100,
        4,
    )

    result[
        "sma50_vs_sma200_percent"
    ] = round(
        (
            (sma50 - sma200)
            / sma200
        )
        * 100,
        4,
    )

    if (
        close > sma20
        and sma20 > sma50
        and sma50 > sma200
    ):
        alignment = (
            "STRONG_UPTREND"
        )

    elif (
        close > sma50
        and sma50 > sma200
    ):
        alignment = "UPTREND"

    elif (
        close < sma50
        and sma50 < sma200
    ):
        alignment = "DOWNTREND"

    else:
        alignment = "MIXED"

    result[
        "trend_alignment"
    ] = alignment

    result["status"] = (
        "AVAILABLE"
    )

    result["reason"] = ""

    return result


if __name__ == "__main__":
    from pprint import pprint

    pprint(
        calculate_moving_average_context(
            symbol="CNR.TO",
            measurement_date="2026-07-17",
        )
    )