"""
Northstar Quant
Trade Path Research Analysis

Reconstructs the intraday one-minute path of completed paper
trades for post-validation stop, target and holding-period
research.

This module is observational only. It never changes trade
decisions, exits, stops, targets, sizing or strategy rules.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from core.ibkr_data_provider import (
    IBKRDataProvider,
)
from paper_trading.morning_database import (
    save_trade_minute_bars,
)


TORONTO_TIMEZONE = ZoneInfo(
    "America/Toronto"
)

TRADE_PATH_IBKR_CLIENT_ID = 19


def normalize_bar_datetime(
    value,
):
    """
    Convert an IBKR bar timestamp to Toronto time.
    """

    if hasattr(
        value,
        "to_pydatetime",
    ):
        value = value.to_pydatetime()

    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=TORONTO_TIMEZONE
            )

        return value.astimezone(
            TORONTO_TIMEZONE
        )

    text_value = str(
        value
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
        f"{value}"
    )


def trade_path_window(
    trade,
):
    """
    Build the effective research window.

    Paper entries use the official opening price, so the
    research window begins at 09:30 Toronto time.

    If an exact exit timestamp was recorded, bars after that
    timestamp are excluded.
    """

    entry_date = datetime.strptime(
        str(trade["entry_date"]),
        "%Y-%m-%d",
    ).date()

    start = datetime.combine(
        entry_date,
        time(9, 30),
        tzinfo=TORONTO_TIMEZONE,
    )

    exit_timestamp = str(
        trade.get(
            "exit_timestamp",
            "",
        )
        or ""
    ).strip()

    if exit_timestamp:
        end = datetime.fromisoformat(
            exit_timestamp
        )

        if end.tzinfo is None:
            end = end.replace(
                tzinfo=TORONTO_TIMEZONE
            )
        else:
            end = end.astimezone(
                TORONTO_TIMEZONE
            )

        return start, end

    exit_date_text = str(
        trade.get(
            "exit_date",
            trade["entry_date"],
        )
    )

    exit_date = datetime.strptime(
        exit_date_text,
        "%Y-%m-%d",
    ).date()

    end = datetime.combine(
        exit_date,
        time(16, 0),
        tzinfo=TORONTO_TIMEZONE,
    )

    return start, end


def normalize_trade_bars(
    trade,
    raw_bars,
):
    """
    Normalize and restrict IBKR bars to the actual trade window.
    """

    start, end = trade_path_window(
        trade
    )

    normalized = []

    for bar in raw_bars:
        try:
            timestamp = (
                normalize_bar_datetime(
                    bar.date
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if timestamp < start:
            continue

        if timestamp > end:
            continue

        normalized.append(
            {
                "bar_timestamp": (
                    timestamp.isoformat()
                ),
                "bar_date": (
                    timestamp.date().isoformat()
                ),
                "bar_time": (
                    timestamp.time()
                    .replace(
                        tzinfo=None
                    )
                    .isoformat(
                        timespec="seconds"
                    )
                ),
                "open_price": float(
                    bar.open
                ),
                "high_price": float(
                    bar.high
                ),
                "low_price": float(
                    bar.low
                ),
                "close_price": float(
                    bar.close
                ),
                "volume": int(
                    float(
                        bar.volume
                        or 0
                    )
                ),
                "data_source": (
                    "IBKR_ONE_MINUTE"
                ),
            }
        )

    normalized.sort(
        key=lambda row: row[
            "bar_timestamp"
        ]
    )

    return normalized


def calculate_trade_path_metrics(
    trade,
    bars,
):
    """
    Calculate MFE/MAE from normalized one-minute OHLCV bars.
    """

    if not bars:
        return {
            "trade_path_status": "NO_DATA",
            "trade_path_source": "IBKR_ONE_MINUTE",
            "trade_path_bar_count": 0,
        }

    entry_price = float(
        trade["entry_price"]
    )

    shares = int(
        trade.get(
            "shares",
            0,
        )
        or 0
    )

    stop_price = float(
        trade.get(
            "stop_price",
            entry_price,
        )
        or entry_price
    )

    initial_risk_per_share = max(
        entry_price - stop_price,
        0.0,
    )

    highest_bar = max(
        bars,
        key=lambda row: float(
            row["high_price"]
        ),
    )

    lowest_bar = min(
        bars,
        key=lambda row: float(
            row["low_price"]
        ),
    )

    highest_price = float(
        highest_bar["high_price"]
    )

    lowest_price = float(
        lowest_bar["low_price"]
    )

    mfe_per_share = max(
        highest_price - entry_price,
        0.0,
    )

    mae_per_share = max(
        entry_price - lowest_price,
        0.0,
    )

    mfe_amount = (
        mfe_per_share * shares
    )

    mae_amount = (
        mae_per_share * shares
    )

    mfe_percent = (
        mfe_per_share
        / entry_price
        * 100
        if entry_price > 0
        else 0.0
    )

    mae_percent = (
        mae_per_share
        / entry_price
        * 100
        if entry_price > 0
        else 0.0
    )

    mfe_r = (
        mfe_per_share
        / initial_risk_per_share
        if initial_risk_per_share > 0
        else 0.0
    )

    mae_r = (
        mae_per_share
        / initial_risk_per_share
        if initial_risk_per_share > 0
        else 0.0
    )

    return {
        "trade_path_status": "COMPLETE",
        "trade_path_source": (
            "IBKR_ONE_MINUTE"
        ),
        "trade_path_bar_count": (
            len(bars)
        ),
        "highest_price": round(
            highest_price,
            6,
        ),
        "lowest_price": round(
            lowest_price,
            6,
        ),
        "mfe_amount": round(
            mfe_amount,
            6,
        ),
        "mfe_percent": round(
            mfe_percent,
            6,
        ),
        "mfe_r": round(
            mfe_r,
            6,
        ),
        "mfe_timestamp": (
            highest_bar[
                "bar_timestamp"
            ]
        ),
        "mae_amount": round(
            mae_amount,
            6,
        ),
        "mae_percent": round(
            mae_percent,
            6,
        ),
        "mae_r": round(
            mae_r,
            6,
        ),
        "mae_timestamp": (
            lowest_bar[
                "bar_timestamp"
            ]
        ),
    }


def capture_trade_path(
    trade,
    provider=None,
    database_file=None,
):
    """
    Retrieve, persist and analyze one completed trade path.

    Failure is returned as research status data rather than
    raising into the trading engine.
    """

    owns_provider = (
        provider is None
    )

    if provider is None:
        provider = IBKRDataProvider(
            client_id=(
                TRADE_PATH_IBKR_CLIENT_ID
            )
        )

    try:
        raw_bars = (
            provider.get_historical_bars(
                symbol=trade["symbol"],
                duration="3 W",
                bar_size="1 min",
                use_rth=True,
                what_to_show="TRADES",
            )
        )

        bars = normalize_trade_bars(
            trade,
            raw_bars,
        )

        if database_file is None:
            save_result = (
                save_trade_minute_bars(
                    trade,
                    bars,
                )
            )
        else:
            save_result = (
                save_trade_minute_bars(
                    trade,
                    bars,
                    database_file=(
                        database_file
                    ),
                )
            )

        metrics = (
            calculate_trade_path_metrics(
                trade,
                bars,
            )
        )

        metrics[
            "trade_path_bars_saved"
        ] = save_result.get(
            "bars_inserted",
            0,
        )

        return metrics

    except Exception as error:
        return {
            "trade_path_status": "ERROR",
            "trade_path_source": "IBKR",
            "trade_path_bar_count": 0,
            "trade_path_bars_saved": 0,
            "trade_path_error": str(
                error
            ),
        }

    finally:
        if owns_provider:
            provider.disconnect()
