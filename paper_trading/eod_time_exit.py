"""
Northstar Quant
End-of-Day Maximum Hold Exit Service

Closes positions on their exact maximum holding day using
the completed TSX daily closing price.

This keeps paper trading aligned with the historical simulator:
- entry session is Day 1
- stops and targets remain active through Day 10
- otherwise exit at the Day-10 close
"""

from datetime import date, datetime

from core.ibkr_data_provider import IBKRDataProvider
from core.market_hours import (
    TORONTO_TIMEZONE,
    get_tsx_market_close_time,
)
from paper_trading.position_manager import (
    count_trading_days,
)


EOD_TIME_EXIT_IBKR_CLIENT_ID = 31


def normalize_trading_date(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(
                tzinfo=TORONTO_TIMEZONE
            )
        else:
            value = value.astimezone(
                TORONTO_TIMEZONE
            )

        return value.date()

    if isinstance(value, date):
        return value

    return datetime.strptime(
        str(value),
        "%Y-%m-%d",
    ).date()


def normalize_bar_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.strptime(
        str(value)[:10],
        "%Y-%m-%d",
    ).date()


def get_ibkr_daily_close(
    provider,
    symbol,
    trading_date,
):
    bars = provider.get_historical_bars(
        symbol=symbol,
        duration="5 D",
        bar_size="1 day",
        use_rth=True,
        what_to_show="TRADES",
    )

    for bar in reversed(list(bars)):
        if (
            normalize_bar_date(bar.date)
            != trading_date
        ):
            continue

        return float(bar.close)

    raise ValueError(
        "No IBKR daily closing price "
        f"available for {symbol} on "
        f"{trading_date.isoformat()}."
    )


def collect_due_positions(
    engines,
    trading_date,
):
    date_text = trading_date.isoformat()
    due = []

    for strategy_name, engine in engines.items():
        if engine is None:
            continue

        refresh = getattr(
            engine,
            "refresh_runtime_state",
            None,
        )

        if callable(refresh):
            refresh()

        portfolio = getattr(
            engine,
            "portfolio",
            None,
        )

        if portfolio is None:
            continue

        for position in list(
            getattr(
                portfolio,
                "open_positions",
                [],
            )
        ):
            entry_date = position.get(
                "entry_date"
            )

            if not entry_date:
                continue

            max_hold_days = int(
                position.get(
                    "max_hold_days",
                    10,
                )
                or 10
            )

            trading_days_held = (
                count_trading_days(
                    entry_date,
                    date_text,
                )
            )

            # Only the exact scheduled Day-10 exit
            # belongs in this EOD service.
            if (
                trading_days_held
                != max_hold_days
            ):
                continue

            due.append(
                (
                    strategy_name,
                    engine,
                    position,
                )
            )

    return due


def run_eod_time_exits(
    engines,
    current_date,
    provider=None,
):
    trading_date = normalize_trading_date(
        current_date
    )

    due = collect_due_positions(
        engines,
        trading_date,
    )

    if not due:
        return {
            "success": True,
            "status": "NO_EXITS_DUE",
            "date": trading_date.isoformat(),
            "due": 0,
            "closed": 0,
            "results": [],
            "errors": [],
        }

    owns_provider = provider is None

    if provider is None:
        provider = IBKRDataProvider(
            client_id=(
                EOD_TIME_EXIT_IBKR_CLIENT_ID
            )
        )

    results = []
    errors = []
    close_cache = {}

    market_close = (
        get_tsx_market_close_time(
            trading_date
        )
    )

    exit_timestamp = datetime.combine(
        trading_date,
        market_close,
        tzinfo=TORONTO_TIMEZONE,
    )

    try:
        for (
            strategy_name,
            engine,
            position,
        ) in due:
            symbol = position["symbol"]

            try:
                if symbol not in close_cache:
                    close_cache[symbol] = (
                        get_ibkr_daily_close(
                            provider,
                            symbol,
                            trading_date,
                        )
                    )

                exit_price = close_cache[
                    symbol
                ]

                market_snapshot = {
                    "symbol": symbol,
                    "price": exit_price,
                    "close": exit_price,
                    "data_source": "IBKR",
                    "source": "IBKR",
                    "price_source": (
                        "IBKR_DAILY_CLOSE"
                    ),
                    "quote_timestamp": (
                        exit_timestamp.isoformat(
                            timespec="seconds"
                        )
                    ),
                }

                result = engine.close_position(
                    symbol=symbol,
                    exit_price=exit_price,
                    current_date=(
                        trading_date.isoformat()
                    ),
                    exit_reason="Time exit",
                    current_datetime=(
                        exit_timestamp
                    ),
                    market_snapshot=(
                        market_snapshot
                    ),
                )

                if not result.get(
                    "success",
                    False,
                ):
                    raise RuntimeError(
                        result.get(
                            "message",
                            "Position close failed.",
                        )
                    )

                results.append(
                    {
                        "strategy": (
                            strategy_name
                        ),
                        "symbol": symbol,
                        "exit_date": (
                            trading_date.isoformat()
                        ),
                        "exit_price": exit_price,
                        "exit_reason": (
                            "Time exit"
                        ),
                    }
                )

            except Exception as error:
                errors.append(
                    {
                        "strategy": (
                            strategy_name
                        ),
                        "symbol": symbol,
                        "message": str(error),
                    }
                )

    finally:
        if owns_provider:
            provider.disconnect()

    return {
        "success": not errors,
        "status": (
            "COMPLETED"
            if not errors
            else "ERROR"
        ),
        "date": trading_date.isoformat(),
        "due": len(due),
        "closed": len(results),
        "results": results,
        "errors": errors,
    }
