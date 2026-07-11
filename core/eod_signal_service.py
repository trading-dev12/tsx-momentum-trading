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
    MARKET_CLOSE_TIME,
    TORONTO_TIMEZONE,
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
    - today is Monday through Friday; and
    - Toronto time is 4:00 PM or later.

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

    if current_datetime.weekday() >= 5:
        return False

    current_time = (
        current_datetime.time().replace(tzinfo=None)
    )

    return current_time >= MARKET_CLOSE_TIME


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

    return {
        "symbol": symbol,
        "signal_date": signal_row["date"],
        "close": signal_row["close"],
        "atr": atr,
        "tmqs": signal["tmqs"],
        "rvol": signal["rvol"],
        "breakout": signal["breakout"],
        "decision": signal["decision"],
        "reason": signal["reason"],
        "breakout_score": signal.get(
            "breakout_score",
            0,
        ),
        "volume_score": signal.get(
            "volume_score",
            0,
        ),
        "price_score": signal.get(
            "price_score",
            0,
        ),
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