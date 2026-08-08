"""
Northstar Quant
IBKR Historical Research Data

Read-only normalized historical-data layer for research modules.

This module does not modify signals, strategy rules, positions,
pending trades, portfolios, or journals.
"""

import pandas as pd

from core.ibkr_data_provider import (
    IBKRDataProvider,
)


RESEARCH_IBKR_CLIENT_ID = 17

DAILY_COLUMNS = [
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def _bars_to_dataframe(bars):
    """
    Convert IBKR historical bars into a normalized DataFrame.
    """

    rows = []

    for bar in bars:
        rows.append(
            {
                "date": bar.date,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=DAILY_COLUMNS
        )

    frame = pd.DataFrame(
        rows,
        columns=DAILY_COLUMNS,
    )

    frame["date"] = pd.to_datetime(
        frame["date"],
        errors="coerce",
    )

    frame = frame.dropna(
        subset=["date"]
    )

    frame = frame.sort_values(
        "date"
    )

    frame = frame.drop_duplicates(
        subset=["date"],
        keep="last",
    )

    return frame.reset_index(
        drop=True
    )


def load_ibkr_daily_history(
    symbol,
    measurement_date=None,
    duration="2 Y",
    adjusted=True,
    provider=None,
    client_id=RESEARCH_IBKR_CLIENT_ID,
):
    """
    Load normalized IBKR daily OHLCV history.

    adjusted=True uses ADJUSTED_LAST for research calculations
    that should account for stock splits and dividends.

    measurement_date prevents future information from entering
    historical research calculations.
    """

    owns_provider = (
        provider is None
    )

    if provider is None:
        provider = IBKRDataProvider(
            client_id=client_id
        )

    what_to_show = (
        "ADJUSTED_LAST"
        if adjusted
        else "TRADES"
    )

    try:
        bars = (
            provider.get_historical_bars(
                symbol=symbol,
                duration=duration,
                bar_size="1 day",
                use_rth=True,
                what_to_show=(
                    what_to_show
                ),
            )
        )

        frame = _bars_to_dataframe(
            bars
        )

        if measurement_date is not None:
            cutoff = pd.Timestamp(
                measurement_date
            ).normalize()

            frame = frame[
                frame["date"].dt.normalize()
                <= cutoff
            ].copy()

            frame = frame.reset_index(
                drop=True
            )

        frame.attrs[
            "data_source"
        ] = "IBKR"

        frame.attrs[
            "historical_data_type"
        ] = what_to_show

        frame.attrs[
            "symbol"
        ] = str(
            symbol
        ).upper()

        return frame

    finally:
        if owns_provider:
            provider.disconnect()
