"""
Morning Market Recorder

Records timestamped one-minute observations for pending
paper-trade candidates.

This module is research-only. It does not open, close, delay,
approve, reject, or otherwise modify paper trades.
"""

from datetime import datetime

import yfinance as yf

from core.ibkr_data_provider import IBKRDataProvider
from core.market_hours import TORONTO_TIMEZONE
from paper_trading.morning_database import (
    DEFAULT_DATABASE_FILE,
    save_observation,
)
from paper_trading.opening_price import normalize_symbol


MORNING_RESEARCH_IBKR_CLIENT_ID = 18


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


def read_numeric_value(value):
    """
    Convert a scalar or one-item pandas Series to float.
    """

    if hasattr(value, "iloc"):
        value = value.iloc[0]

    return float(value)


def get_latest_yahoo_one_minute_bar(
    symbol,
    current_datetime=None,
):
    """
    Return the latest available regular-session one-minute bar
    for the exact Toronto calendar date.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    observation_date = (
        current_datetime.date().isoformat()
    )

    yahoo_symbol = normalize_symbol(symbol)

    try:
        history = yf.Ticker(yahoo_symbol).history(
            period="1d",
            interval="1m",
            auto_adjust=False,
            prepost=False,
        )

    except Exception as error:
        return {
            "success": False,
            "symbol": yahoo_symbol,
            "message": (
                f"One-minute data download failed: {error}"
            ),
        }

    if history is None or history.empty:
        return {
            "success": False,
            "symbol": yahoo_symbol,
            "message": "No one-minute data is available.",
        }

    matching_rows = []

    for row_index, row in history.iterrows():
        row_datetime = row_index.to_pydatetime()

        if row_datetime.tzinfo is None:
            row_datetime = row_datetime.replace(
                tzinfo=TORONTO_TIMEZONE,
            )
        else:
            row_datetime = row_datetime.astimezone(
                TORONTO_TIMEZONE,
            )

        if row_datetime.date().isoformat() != observation_date:
            continue

        if row_datetime > current_datetime:
            continue

        matching_rows.append(
            (
                row_datetime,
                row,
            )
        )

    if not matching_rows:
        return {
            "success": False,
            "symbol": yahoo_symbol,
            "message": (
                "No matching one-minute bar is available "
                f"for {observation_date}."
            ),
        }

    latest_datetime, latest_row = matching_rows[-1]

    try:
        open_price = read_numeric_value(
            latest_row["Open"]
        )

        high_price = read_numeric_value(
            latest_row["High"]
        )

        low_price = read_numeric_value(
            latest_row["Low"]
        )

        close_price = read_numeric_value(
            latest_row["Close"]
        )

        volume = int(
            read_numeric_value(
                latest_row["Volume"]
            )
        )

        cumulative_volume = sum(
            int(
                read_numeric_value(
                    row["Volume"]
                )
            )
            for _, row in matching_rows
        )

    except (
        KeyError,
        TypeError,
        ValueError,
        IndexError,
    ) as error:
        return {
            "success": False,
            "symbol": yahoo_symbol,
            "message": (
                f"One-minute bar could not be read: {error}"
            ),
        }

    return {
        "success": True,
        "symbol": yahoo_symbol,
        "bar_timestamp": latest_datetime,
        "open_price": open_price,
        "high_price": high_price,
        "low_price": low_price,
        "close_price": close_price,
        "volume": volume,
        "cumulative_volume": cumulative_volume,
        "data_source": "YAHOO_ONE_MINUTE",
    }


def normalize_ibkr_bar_datetime(
    bar_date,
):
    """
    Normalize an IBKR historical-bar timestamp to Toronto time.
    """

    if hasattr(
        bar_date,
        "to_pydatetime",
    ):
        bar_date = (
            bar_date.to_pydatetime()
        )

    if isinstance(
        bar_date,
        datetime,
    ):
        if bar_date.tzinfo is None:
            return bar_date.replace(
                tzinfo=TORONTO_TIMEZONE
            )

        return bar_date.astimezone(
            TORONTO_TIMEZONE
        )

    text_value = str(
        bar_date
    ).strip()

    formats = [
        "%Y%m%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for format_string in formats:
        try:
            parsed = datetime.strptime(
                text_value[:19],
                format_string,
            )

            return parsed.replace(
                tzinfo=TORONTO_TIMEZONE
            )

        except ValueError:
            continue

    raise ValueError(
        "Unsupported IBKR bar timestamp: "
        f"{bar_date}"
    )


def get_latest_ibkr_one_minute_bar(
    symbol,
    current_datetime=None,
    provider=None,
):
    """
    Return the latest regular-session one-minute IBKR bar.

    This is research-only and does not affect execution.
    """

    current_datetime = (
        normalize_current_datetime(
            current_datetime
        )
    )

    owns_provider = (
        provider is None
    )

    if provider is None:
        provider = IBKRDataProvider(
            client_id=(
                MORNING_RESEARCH_IBKR_CLIENT_ID
            )
        )

    try:
        bars = provider.get_historical_bars(
            symbol=symbol,
            duration="2 D",
            bar_size="1 min",
            use_rth=True,
            what_to_show="TRADES",
        )

        matching_bars = []

        for bar in bars:
            try:
                bar_datetime = (
                    normalize_ibkr_bar_datetime(
                        bar.date
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if (
                bar_datetime.date()
                != current_datetime.date()
            ):
                continue

            if (
                bar_datetime
                > current_datetime
            ):
                continue

            matching_bars.append(
                (
                    bar_datetime,
                    bar,
                )
            )

        if not matching_bars:
            return {
                "success": False,
                "symbol": symbol,
                "message": (
                    "No matching IBKR one-minute "
                    "bar is available."
                ),
            }

        matching_bars.sort(
            key=lambda item: item[0]
        )

        latest_datetime, latest_bar = (
            matching_bars[-1]
        )

        cumulative_volume = sum(
            int(
                float(
                    getattr(
                        bar,
                        "volume",
                        0,
                    )
                    or 0
                )
            )
            for _, bar in matching_bars
        )

        return {
            "success": True,
            "symbol": str(
                symbol
            ).upper(),
            "bar_timestamp": (
                latest_datetime
            ),
            "open_price": float(
                latest_bar.open
            ),
            "high_price": float(
                latest_bar.high
            ),
            "low_price": float(
                latest_bar.low
            ),
            "close_price": float(
                latest_bar.close
            ),
            "volume": int(
                float(
                    latest_bar.volume
                    or 0
                )
            ),
            "cumulative_volume": (
                cumulative_volume
            ),
            "data_source": (
                "IBKR_ONE_MINUTE"
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "symbol": str(
                symbol
            ).upper(),
            "message": (
                "IBKR one-minute data "
                f"unavailable: {error}"
            ),
        }

    finally:
        if owns_provider:
            provider.disconnect()


def get_latest_one_minute_bar(
    symbol,
    current_datetime=None,
):
    """
    Retrieve one-minute research data using:

    1. IBKR historical one-minute bars
    2. Yahoo one-minute fallback

    Provider provenance is retained in the observation.
    """

    ibkr_result = (
        get_latest_ibkr_one_minute_bar(
            symbol,
            current_datetime,
        )
    )

    if ibkr_result.get(
        "success"
    ):
        return ibkr_result

    yahoo_result = (
        get_latest_yahoo_one_minute_bar(
            symbol,
            current_datetime,
        )
    )

    if yahoo_result.get(
        "success"
    ):
        yahoo_result = dict(
            yahoo_result
        )

        yahoo_result[
            "data_source"
        ] = (
            "YAHOO_ONE_MINUTE_FALLBACK"
        )

        yahoo_result[
            "primary_source_error"
        ] = ibkr_result.get(
            "message",
            "",
        )

    return yahoo_result


def build_observation(
    pending_trade,
    bar_result,
):
    """
    Combine one pending signal with one market-data observation.
    """

    bar_timestamp = bar_result["bar_timestamp"]

    signal_close = float(
        pending_trade["signal_close"]
    )

    open_price = float(
        bar_result["open_price"]
    )

    close_price = float(
        bar_result["close_price"]
    )

    gap_percent = (
        ((open_price - signal_close) / signal_close) * 100
        if signal_close > 0
        else 0.0
    )

    distance_from_open_percent = (
        ((close_price - open_price) / open_price) * 100
        if open_price > 0
        else 0.0
    )

    previous_high = pending_trade.get(
        "previous_high"
    )

    if previous_high:
        previous_high = float(previous_high)

        distance_from_previous_high_percent = (
            (
                (close_price - previous_high)
                / previous_high
            )
            * 100
        )
    else:
        distance_from_previous_high_percent = None

    return {
        "symbol": pending_trade["symbol"],
        "signal_date": pending_trade["signal_date"],
        "observation_date": (
            bar_timestamp.date().isoformat()
        ),
        "observation_time": (
            bar_timestamp.strftime("%H:%M:%S")
        ),
        "observation_timestamp": (
            bar_timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ),
        "open_price": open_price,
        "high_price": float(
            bar_result["high_price"]
        ),
        "low_price": float(
            bar_result["low_price"]
        ),
        "close_price": close_price,
        "volume": int(
            bar_result["volume"]
        ),
        "cumulative_volume": int(
            bar_result["cumulative_volume"]
        ),
        "previous_close": signal_close,
        "previous_high": previous_high,
        "gap_percent": round(
            gap_percent,
            4,
        ),
        "distance_from_open_percent": round(
            distance_from_open_percent,
            4,
        ),
        "distance_from_previous_high_percent": (
            round(
                distance_from_previous_high_percent,
                4,
            )
            if distance_from_previous_high_percent
            is not None
            else None
        ),
        "atr": float(
            pending_trade["atr"]
        ),
        "tmqs": float(
            pending_trade["tmqs"]
        ),
        "rvol": float(
            pending_trade["rvol"]
        ),
        "breakout": pending_trade["breakout"],
        "baseline_entry_price": (
            pending_trade.get(
                "baseline_entry_price"
            )
        ),
        "data_source": bar_result["data_source"],
    }


def record_pending_candidates_once(
    paper_engine,
    current_datetime=None,
    bar_provider=get_latest_one_minute_bar,
    database_file=DEFAULT_DATABASE_FILE,
    pending_trades=None,
):
    """
    Record one observation for each supplied candidate.

    When pending_trades is not supplied, candidates are read from
    the live pending-trade queue.

    A supplied candidate list allows a background recorder service
    to continue observing an immutable morning snapshot after the
    execution engine removes completed trades from the live queue.

    The queue and portfolio are never modified.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    if pending_trades is None:
        candidates = (
            paper_engine.pending_trades.get_all()
        )
    else:
        candidates = [
            dict(candidate)
            for candidate in pending_trades
        ]

    results = []

    for pending_trade in candidates:
        symbol = pending_trade["symbol"]

        bar_result = bar_provider(
            symbol,
            current_datetime,
        )

        if not bar_result.get("success"):
            results.append(
                {
                    "success": False,
                    "symbol": symbol,
                    "inserted": False,
                    "message": bar_result.get(
                        "message",
                        "One-minute bar unavailable.",
                    ),
                }
            )
            continue

        observation = build_observation(
            pending_trade,
            bar_result,
        )

        save_result = save_observation(
            observation,
            database_file=database_file,
        )

        results.append(
            {
                "success": save_result["success"],
                "symbol": symbol,
                "inserted": save_result["inserted"],
                "message": save_result["message"],
                "observation": observation,
            }
        )

    inserted = sum(
        1
        for result in results
        if result.get("inserted")
    )

    unavailable = sum(
        1
        for result in results
        if not result.get("success")
    )

    duplicates = sum(
        1
        for result in results
        if (
            result.get("success")
            and not result.get("inserted")
        )
    )

    return {
        "observation_date": (
            current_datetime.date().isoformat()
        ),
        "candidates_checked": len(candidates),
        "inserted": inserted,
        "duplicates": duplicates,
        "unavailable": unavailable,
        "results": results,
    }