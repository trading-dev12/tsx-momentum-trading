"""
End-of-Day Signal Service

Generates trading signals from completed daily candles only.

Today's candle is:
- excluded before the TSX closes;
- included after the TSX closes;
- never treated as completed on weekends.

The complete watchlist is downloaded in one batch to avoid
making a separate Yahoo Finance request for every symbol.
"""

from datetime import datetime

import yfinance as yf

from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import calculate_atr
from core.market_hours import (
    TORONTO_TIMEZONE,
    get_tsx_market_close_time,
    is_tsx_trading_day,
)

from core.watchlist_loader import load_all_watchlists


def normalize_yahoo_symbol(symbol):
    """
    Convert a project symbol into its Yahoo Finance symbol.
    """

    return symbol if symbol.endswith(".TO") else f"{symbol}.TO"


def normalize_current_datetime(current_datetime=None):
    """
    Return a timezone-aware Toronto datetime.
    """

    if current_datetime is None:
        return datetime.now(TORONTO_TIMEZONE)

    if current_datetime.tzinfo is None:
        return current_datetime.replace(
            tzinfo=TORONTO_TIMEZONE,
        )

    return current_datetime.astimezone(
        TORONTO_TIMEZONE,
    )


def is_daily_candle_complete(
    row_date,
    current_datetime=None,
):
    """
    Determine whether a daily candle is complete.

    Previous calendar dates are complete.

    Today's candle is complete only when:
    - today is a TSX trading day; and
    - Toronto time is at or after that day's TSX close.

    Future dates are never complete.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    today = current_datetime.date()

    if row_date < today:
        return True

    if row_date > today:
        return False

    if not is_tsx_trading_day(today):
        return False

    current_time = (
        current_datetime.time().replace(
            tzinfo=None
        )
    )

    market_close_time = get_tsx_market_close_time(
        today
    )

    return current_time >= market_close_time

def download_watchlist_history(
    watchlist,
    period="10d",
):
    """
    Download daily history for the complete watchlist.
    """

    yahoo_symbols = [
        normalize_yahoo_symbol(symbol)
        for symbol in watchlist
    ]

    history = yf.download(
        tickers=yahoo_symbols,
        period=period,
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False,
    )

    return history


def get_completed_daily_rows_from_batch(
    history,
    symbol,
    current_datetime=None,
):
    """
    Extract completed daily candles for one symbol from the
    batch history response.
    """

    yahoo_symbol = normalize_yahoo_symbol(symbol)

    if history is None or history.empty:
        return []

    try:
        symbol_history = history[yahoo_symbol]
    except (KeyError, TypeError):
        return []

    if (
        symbol_history is None
        or symbol_history.empty
    ):
        return []

    completed_rows = []

    for index, row in symbol_history.iterrows():
        row_date = index.date()

        if not is_daily_candle_complete(
            row_date,
            current_datetime=current_datetime,
        ):
            continue

        open_price = row.get("Open")
        high_price = row.get("High")
        low_price = row.get("Low")
        close_price = row.get("Close")
        volume = row.get("Volume")

        required_values = [
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
        ]

        if any(
            value != value
            for value in required_values
        ):
            continue

        completed_rows.append(
            {
                "date": row_date.strftime("%Y-%m-%d"),
                "open": float(open_price),
                "high": float(high_price),
                "low": float(low_price),
                "close": float(close_price),
                "volume": int(volume),
            }
        )

    return completed_rows


def build_eod_signal_from_rows(
    symbol,
    rows,
):
    """
    Build one end-of-day signal from completed daily rows.
    """

    if len(rows) < 2:
        return None

    previous_row = rows[-2]
    signal_row = rows[-1]
    signal_index = len(rows) - 1

    atr = calculate_atr(
        rows,
        signal_index,
    )

    signal = evaluate_historical_setup(
        signal_row,
        previous_row,
    )

    signal_open = float(
        signal_row["open"]
    )
    signal_high = float(
        signal_row["high"]
    )
    signal_low = float(
        signal_row["low"]
    )
    signal_close = float(
        signal_row["close"]
    )
    signal_volume = int(
        signal_row["volume"]
    )

    previous_open = float(
        previous_row["open"]
    )
    previous_high = float(
        previous_row["high"]
    )
    previous_low = float(
        previous_row["low"]
    )
    previous_close = float(
        previous_row["close"]
    )
    previous_volume = int(
        previous_row["volume"]
    )

    gap_percent = (
        (
            (signal_open - previous_close)
            / previous_close
        )
        * 100
        if previous_close > 0
        else 0.0
    )

    price_change_percent = (
        (
            (signal_close - previous_close)
            / previous_close
        )
        * 100
        if previous_close > 0
        else 0.0
    )

    breakout_percent = (
        (
            (signal_close - previous_high)
            / previous_high
        )
        * 100
        if previous_high > 0
        else 0.0
    )

    atr_percent = (
        (float(atr) / signal_close) * 100
        if atr is not None and signal_close > 0
        else 0.0
    )

    dollar_volume = (
        signal_close
        * signal_volume
    )

    breakout_score = float(
        signal.get(
            "breakout_score",
            0,
        )
        or 0
    )

    volume_score = float(
        signal.get(
            "volume_score",
            0,
        )
        or 0
    )

    price_score = float(
        signal.get(
            "price_score",
            0,
        )
        or 0
    )

    pre_cap_score = (
        breakout_score
        + volume_score
        + price_score
    )

    final_tmqs = float(
        signal.get(
            "tmqs",
            0,
        )
        or 0
    )

    quality_cap_points_removed = max(
        0.0,
        pre_cap_score - final_tmqs,
    )

    return {
        "symbol": symbol,
        "strategy": "MOMENTUM",
        "signal_date": signal_row["date"],
        "open": signal_open,
        "high": signal_high,
        "low": signal_low,
        "close": signal_close,
        "volume": signal_volume,
        "previous_open": previous_open,
        "previous_high": previous_high,
        "previous_low": previous_low,
        "previous_close": previous_close,
        "previous_volume": previous_volume,
        "gap_percent": round(
            gap_percent,
            6,
        ),
        "price_change_percent": round(
            price_change_percent,
            6,
        ),
        "breakout_percent": round(
            breakout_percent,
            6,
        ),
        "dollar_volume": round(
            dollar_volume,
            2,
        ),
        "atr": atr,
        "atr_percent": round(
            atr_percent,
            6,
        ),
        "tmqs": signal["tmqs"],
        "rvol": signal["rvol"],
        "breakout": signal["breakout"],
        "decision": signal["decision"],
        "reason": signal["reason"],
        "breakout_score": round(
            breakout_score,
            2,
        ),
        "volume_score": round(
            volume_score,
            2,
        ),
        "price_score": round(
            price_score,
            2,
        ),
        "pre_cap_score": round(
            pre_cap_score,
            2,
        ),
        "quality_cap_points_removed": round(
            quality_cap_points_removed,
            2,
        ),
        "data_source": "YAHOO_DAILY_EOD",
    }


def scan_eod_signals(
    watchlist=None,
    current_datetime=None,
):
    """
    Scan the complete TSX watchlist using one batch download.
    """

    if watchlist is None:
        watchlist = load_all_watchlists()

    all_signals = []
    ready_signals = []
    watch_signals = []
    ignored_signals = []
    errors = []

    history = download_watchlist_history(
        watchlist,
        period="3mo",
    )

    for symbol in watchlist:
        try:
            rows = get_completed_daily_rows_from_batch(
                history,
                symbol,
                current_datetime=current_datetime,
            )

            signal = build_eod_signal_from_rows(
                symbol,
                rows,
            )

            if signal is None:
                errors.append(
                    {
                        "symbol": symbol,
                        "error": (
                            "Insufficient completed daily data"
                        ),
                    }
                )
                continue

            all_signals.append(signal)

            decision = signal["decision"]

            if decision == "READY":
                ready_signals.append(signal)

            elif decision == "WATCH":
                watch_signals.append(signal)

            else:
                ignored_signals.append(signal)

        except Exception as error:
            errors.append(
                {
                    "symbol": symbol,
                    "error": str(error),
                }
            )

    def sort_key(item):
        return (
            item["tmqs"],
            item["rvol"],
        )

    all_signals.sort(
        key=sort_key,
        reverse=True,
    )

    ready_signals.sort(
        key=sort_key,
        reverse=True,
    )

    watch_signals.sort(
        key=sort_key,
        reverse=True,
    )

    ignored_signals.sort(
        key=sort_key,
        reverse=True,
    )

    return {
        "all": all_signals,
        "ready": ready_signals,
        "watch": watch_signals,
        "ignore": ignored_signals,
        "errors": errors,
    }