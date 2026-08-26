"""
Northstar Quant matched XIC benchmark.

Measures each paper strategy against XIC.TO using
the same cumulative capital deployments and the
same entry/exit dates.

IBKR adjusted history + live quote are primary.
Yahoo adjusted history is fallback only.

Read-only analytics. Does not affect trading.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from threading import Lock

import pandas as pd
import yfinance as yf

from core.ibkr_data_provider import (
    IBKRDataProvider,
)
from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


BENCHMARK_SYMBOL = "XIC.TO"

BENCHMARK_IBKR_CLIENT_ID = 27

BENCHMARK_CACHE_SECONDS = 300

_CACHE = {
    "loaded_at": None,
    "required_start": None,
    "required_end": None,
    "snapshot": None,
}

_CACHE_LOCK = Lock()


def _normalize_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.strptime(
        str(value)[:10],
        "%Y-%m-%d",
    ).date()


def _history_price_on_or_after(
    history,
    target_date,
):
    target = _normalize_date(
        target_date
    )

    eligible = [
        row
        for row in history
        if row["date"] >= target
    ]

    if not eligible:
        raise ValueError(
            "No XIC benchmark price on or after "
            f"{target.isoformat()}."
        )

    return eligible[0]


def _history_price_on_or_before(
    history,
    target_date,
):
    target = _normalize_date(
        target_date
    )

    eligible = [
        row
        for row in history
        if row["date"] <= target
    ]

    if not eligible:
        raise ValueError(
            "No XIC benchmark price on or before "
            f"{target.isoformat()}."
        )

    return eligible[-1]


def _frame_to_history(frame):
    history = []

    for _, row in frame.iterrows():
        row_date = pd.Timestamp(
            row["date"]
        ).date()

        close = float(
            row["close"]
        )

        history.append(
            {
                "date": row_date,
                "close": close,
            }
        )

    history.sort(
        key=lambda item: item["date"]
    )

    return history


def _load_ibkr_snapshot(
    required_start,
    required_end,
):
    """
    Primary benchmark source.

    Historical prices:
        IBKR ADJUSTED_LAST

    Current benchmark price:
        IBKR live LAST / midpoint / close
        using the provider's normal quote hierarchy.
    """

    provider = IBKRDataProvider(
        client_id=BENCHMARK_IBKR_CLIENT_ID
    )

    try:
        frame = load_ibkr_daily_history(
            symbol=BENCHMARK_SYMBOL,
            measurement_date=required_end,
            duration="1 Y",
            adjusted=True,
            provider=provider,
        )

        if frame is None or frame.empty:
            raise ValueError(
                "IBKR returned no adjusted XIC history."
            )

        history = _frame_to_history(
            frame
        )

        if not history:
            raise ValueError(
                "IBKR XIC history contained no usable rows."
            )

        if (
            history[0]["date"]
            > required_start
        ):
            raise ValueError(
                "IBKR XIC history does not reach the "
                "required strategy start date."
            )

        #
        # All CLOSED benchmark periods must have
        # historical data through their required end.
        #
        if (
            history[-1]["date"]
            < required_end
        ):
            raise ValueError(
                "IBKR adjusted XIC history is not current "
                f"through required date {required_end}."
            )

        quote = provider.get_quote(
            BENCHMARK_SYMBOL
        )

        current_price = float(
            quote["price"]
        )

        return {
            "benchmark": BENCHMARK_SYMBOL,
            "history": history,
            "current_price": current_price,
            "current_price_source": (
                quote.get(
                    "price_source",
                    "UNKNOWN",
                )
            ),
            "history_through": (
                history[-1]["date"]
                .isoformat()
            ),
            "data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
            "live_source": "IBKR",
        }

    finally:
        provider.disconnect()


def _load_yahoo_snapshot(
    required_start,
    required_end,
):
    """
    Emergency benchmark fallback.

    This source is clearly labelled so we never
    mistake fallback data for IBKR data.
    """

    download_start = (
        required_start
        - timedelta(days=7)
    )

    download_end = (
        max(
            required_end,
            datetime.now().date(),
        )
        + timedelta(days=2)
    )

    frame = yf.download(
        BENCHMARK_SYMBOL,
        start=download_start.isoformat(),
        end=download_end.isoformat(),
        auto_adjust=True,
        progress=False,
    )

    if frame.empty:
        raise ValueError(
            "Yahoo returned no adjusted XIC history."
        )

    if isinstance(
        frame.columns,
        pd.MultiIndex,
    ):
        frame.columns = (
            frame.columns
            .get_level_values(0)
        )

    close_series = (
        frame["Close"]
        .dropna()
    )

    history = []

    for timestamp, value in (
        close_series.items()
    ):
        history.append(
            {
                "date": (
                    pd.Timestamp(
                        timestamp
                    ).date()
                ),
                "close": float(value),
            }
        )

    history.sort(
        key=lambda item: item["date"]
    )

    if not history:
        raise ValueError(
            "Yahoo XIC history contained no usable rows."
        )

    if (
        history[-1]["date"]
        < required_end
    ):
        raise ValueError(
            "Yahoo XIC history is stale for "
            f"required date {required_end}."
        )

    return {
        "benchmark": BENCHMARK_SYMBOL,
        "history": history,
        "current_price": float(
            history[-1]["close"]
        ),
        "current_price_source": (
            "LATEST_ADJUSTED_CLOSE"
        ),
        "history_through": (
            history[-1]["date"]
            .isoformat()
        ),
        "data_source": (
            "YAHOO_ADJUSTED_FALLBACK"
        ),
        "live_source": (
            "YAHOO_DAILY_FALLBACK"
        ),
    }


def load_benchmark_snapshot(
    required_start,
    required_end,
):
    required_start = _normalize_date(
        required_start
    )

    required_end = _normalize_date(
        required_end
    )

    now = datetime.now()

    with _CACHE_LOCK:
        loaded_at = _CACHE[
            "loaded_at"
        ]

        snapshot = _CACHE[
            "snapshot"
        ]

        cache_age = (
            (
                now - loaded_at
            ).total_seconds()
            if loaded_at is not None
            else None
        )

        cache_covers_request = (
            snapshot is not None
            and _CACHE[
                "required_start"
            ] <= required_start
            and _CACHE[
                "required_end"
            ] >= required_end
        )

        if (
            cache_covers_request
            and cache_age is not None
            and cache_age
            < BENCHMARK_CACHE_SECONDS
        ):
            cached = dict(
                snapshot
            )

            cached[
                "cache_status"
            ] = "HIT"

            return cached

        ibkr_error = ""

        try:
            snapshot = (
                _load_ibkr_snapshot(
                    required_start,
                    required_end,
                )
            )

        except Exception as error:
            ibkr_error = str(
                error
            )

            snapshot = (
                _load_yahoo_snapshot(
                    required_start,
                    required_end,
                )
            )

            snapshot[
                "primary_source_error"
            ] = ibkr_error

        snapshot[
            "cache_status"
        ] = "MISS"

        _CACHE.update(
            {
                "loaded_at": now,
                "required_start": (
                    required_start
                ),
                "required_end": (
                    required_end
                ),
                "snapshot": dict(
                    snapshot
                ),
            }
        )

        return snapshot


def calculate_matched_performance(
    open_positions,
    closed_trades,
    current_prices,
    benchmark_snapshot,
):
    """
    Compare Northstar with XIC using the same
    dollars and the same trade date windows.
    """

    history = benchmark_snapshot[
        "history"
    ]

    benchmark_current = float(
        benchmark_snapshot[
            "current_price"
        ]
    )

    cumulative_capital = 0.0

    strategy_pl = 0.0
    benchmark_pl = 0.0

    trades_evaluated = 0
    entry_dates = []

    #
    # CLOSED TRADES
    #
    for trade in closed_trades:
        entry_price = float(
            trade.get(
                "entry_price",
                0,
            )
            or 0
        )

        shares = int(
            trade.get(
                "shares",
                0,
            )
            or 0
        )

        capital = (
            entry_price
            * shares
        )

        entry_date = trade.get(
            "entry_date"
        )

        exit_date = trade.get(
            "exit_date"
        )

        if (
            capital <= 0
            or not entry_date
            or not exit_date
        ):
            continue

        benchmark_entry_row = (
            _history_price_on_or_after(
                history,
                entry_date,
            )
        )

        benchmark_exit_row = (
            _history_price_on_or_before(
                history,
                exit_date,
            )
        )

        benchmark_return = (
            (
                benchmark_exit_row[
                    "close"
                ]
                / benchmark_entry_row[
                    "close"
                ]
            )
            - 1
        )

        actual_pl = float(
            trade.get(
                "profit_loss",
                0,
            )
            or 0
        )

        cumulative_capital += (
            capital
        )

        strategy_pl += actual_pl

        benchmark_pl += (
            capital
            * benchmark_return
        )

        trades_evaluated += 1

        entry_dates.append(
            str(entry_date)[:10]
        )

    #
    # OPEN TRADES
    #
    for trade in open_positions:
        entry_price = float(
            trade.get(
                "entry_price",
                0,
            )
            or 0
        )

        shares = int(
            trade.get(
                "shares",
                0,
            )
            or 0
        )

        capital = (
            entry_price
            * shares
        )

        entry_date = trade.get(
            "entry_date"
        )

        if (
            capital <= 0
            or not entry_date
        ):
            continue

        symbol = str(
            trade.get(
                "symbol",
                "",
            )
        )

        current_price = float(
            current_prices.get(
                symbol,
                entry_price,
            )
            or entry_price
        )

        actual_pl = (
            current_price
            - entry_price
        ) * shares

        benchmark_entry_row = (
            _history_price_on_or_after(
                history,
                entry_date,
            )
        )

        benchmark_return = (
            (
                benchmark_current
                / benchmark_entry_row[
                    "close"
                ]
            )
            - 1
        )

        cumulative_capital += (
            capital
        )

        strategy_pl += actual_pl

        benchmark_pl += (
            capital
            * benchmark_return
        )

        trades_evaluated += 1

        entry_dates.append(
            str(entry_date)[:10]
        )

    strategy_return = (
        (
            strategy_pl
            / cumulative_capital
        )
        * 100
        if cumulative_capital > 0
        else 0.0
    )

    benchmark_return = (
        (
            benchmark_pl
            / cumulative_capital
        )
        * 100
        if cumulative_capital > 0
        else 0.0
    )

    versus_benchmark = (
        strategy_return
        - benchmark_return
    )

    return {
        "status": "AVAILABLE",
        "benchmark": (
            benchmark_snapshot[
                "benchmark"
            ]
        ),
        "trading_since": (
            min(entry_dates)
            if entry_dates
            else "--"
        ),
        "trades_evaluated": (
            trades_evaluated
        ),
        "cumulative_capital": (
            cumulative_capital
        ),
        "strategy_pl": (
            strategy_pl
        ),
        "strategy_return": (
            strategy_return
        ),
        "benchmark_pl": (
            benchmark_pl
        ),
        "benchmark_return": (
            benchmark_return
        ),
        "versus_benchmark": (
            versus_benchmark
        ),
        "dollar_advantage": (
            strategy_pl
            - benchmark_pl
        ),
        "benchmark_history_through": (
            benchmark_snapshot[
                "history_through"
            ]
        ),
        "benchmark_data_source": (
            benchmark_snapshot[
                "data_source"
            ]
        ),
        "benchmark_live_source": (
            benchmark_snapshot[
                "live_source"
            ]
        ),
        "benchmark_price_source": (
            benchmark_snapshot[
                "current_price_source"
            ]
        ),
        "cache_status": (
            benchmark_snapshot.get(
                "cache_status",
                "UNKNOWN",
            )
        ),
        "primary_source_error": (
            benchmark_snapshot.get(
                "primary_source_error",
                "",
            )
        ),
    }


def build_matched_xic_performance(
    open_positions,
    closed_trades,
    current_prices,
    snapshot_loader=load_benchmark_snapshot,
):
    all_trades = (
        list(closed_trades)
        + list(open_positions)
    )

    entry_dates = [
        str(
            trade.get(
                "entry_date",
                "",
            )
        )[:10]
        for trade in all_trades
        if trade.get(
            "entry_date"
        )
    ]

    closed_exit_dates = [
        str(
            trade.get(
                "exit_date",
                "",
            )
        )[:10]
        for trade in closed_trades
        if trade.get(
            "exit_date"
        )
    ]

    if not entry_dates:
        return {
            "status": "AVAILABLE",
            "benchmark": (
                BENCHMARK_SYMBOL
            ),
            "trading_since": "--",
            "trades_evaluated": 0,
            "cumulative_capital": 0.0,
            "strategy_pl": 0.0,
            "strategy_return": 0.0,
            "benchmark_pl": 0.0,
            "benchmark_return": 0.0,
            "versus_benchmark": 0.0,
            "dollar_advantage": 0.0,
            "benchmark_history_through": "--",
            "benchmark_data_source": (
                "NOT_REQUIRED"
            ),
            "benchmark_live_source": (
                "NOT_REQUIRED"
            ),
            "benchmark_price_source": (
                "NOT_REQUIRED"
            ),
            "cache_status": (
                "NOT_REQUIRED"
            ),
            "primary_source_error": "",
        }

    required_start = _normalize_date(
        min(entry_dates)
    )

    #
    # Historical bars only need to cover
    # closed-trade exits and entry dates.
    #
    historical_required_dates = (
        entry_dates
        + closed_exit_dates
    )

    required_end = _normalize_date(
        max(
            historical_required_dates
        )
    )

    try:
        snapshot = snapshot_loader(
            required_start,
            required_end,
        )

        return (
            calculate_matched_performance(
                open_positions,
                closed_trades,
                current_prices,
                snapshot,
            )
        )

    except Exception as error:
        return {
            "status": "UNAVAILABLE",
            "benchmark": (
                BENCHMARK_SYMBOL
            ),
            "reason": str(error),
        }
