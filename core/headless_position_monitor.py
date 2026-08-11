"""
Northstar Headless Position Monitor

Provides one headless position-monitoring cycle for the
paper-trading strategies.

IMPORTANT:
Importing this module does NOT fetch market data,
monitor positions, or modify portfolio state.
"""

import json
from datetime import datetime
from pathlib import Path

from core.market_data import get_quotes


PROJECT_ROOT = Path(__file__).resolve().parent.parent

LATEST_PRICES_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "latest_prices.json"
)


def collect_open_position_symbols(engines):
    # Refresh persisted trading state before determining which
    # positions require live prices. This prevents the long-running
    # headless process from using stale in-memory portfolio data
    # written by another Northstar process.
    for engine in engines.values():
        refresh_runtime_state = getattr(
            engine,
            "refresh_runtime_state",
            None,
        )

        if callable(refresh_runtime_state):
            refresh_runtime_state()

    symbols = {
        position["symbol"]
        for engine in engines.values()
        for position in engine.portfolio.open_positions
    }

    return sorted(symbols)


def build_current_prices(quotes):
    current_prices = {}

    for quote in quotes:
        symbol = quote.get("symbol")
        price = quote.get(
            "price",
            quote.get("close"),
        )

        if symbol and price is not None:
            current_prices[symbol] = float(price)

    return current_prices


def write_latest_prices_snapshot(
    current_prices,
    snapshot_file=LATEST_PRICES_FILE,
    generated_at=None,
):
    """
    Atomically persist current prices for every open
    paper-trading position.
    """

    snapshot_file = Path(
        snapshot_file
    )

    snapshot_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if generated_at is None:
        generated_at = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )

    price_snapshot = {
        "generated_at": generated_at,
        "prices": {
            symbol: float(price)
            for symbol, price
            in current_prices.items()
        },
    }

    temporary_file = (
        snapshot_file.with_suffix(
            ".tmp"
        )
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            price_snapshot,
            file,
            indent=4,
        )

    temporary_file.replace(
        snapshot_file
    )

    return price_snapshot


def run_headless_position_monitor_cycle(
    engines,
    quote_provider=get_quotes,
    current_date=None,
    snapshot_writer=write_latest_prices_snapshot,
):
    """
    Run one position-monitoring cycle across all headless
    paper engines and persist the resulting open-position
    price snapshot.
    """

    symbols = collect_open_position_symbols(
        engines
    )

    if not symbols:
        return {
            "status": "NO_OPEN_POSITIONS",
            "symbols": [],
            "prices": {},
            "closed_trades": {},
            "closed_total": 0,
        }

    quotes = quote_provider(
        symbols
    )

    current_prices = build_current_prices(
        quotes
    )

    if current_prices:
        snapshot_writer(
            current_prices
        )

    if current_date is None:
        current_date = (
            datetime.now().strftime(
                "%Y-%m-%d"
            )
        )

    closed_trades = {}

    for strategy_name, engine in engines.items():
        closed_trades[
            strategy_name
        ] = engine.update_positions(
            latest_prices=current_prices,
            current_date=current_date,
        )

    closed_total = sum(
        len(trades)
        for trades
        in closed_trades.values()
    )

    return {
        "status": "COMPLETED",
        "symbols": symbols,
        "prices": current_prices,
        "closed_trades": closed_trades,
        "closed_total": closed_total,
    }


def refresh_headless_price_snapshot(
    engines,
    quote_provider=get_quotes,
    snapshot_writer=write_latest_prices_snapshot,
):
    """
    Refresh the price snapshot for every open paper
    position without evaluating or closing positions.
    """

    symbols = collect_open_position_symbols(
        engines
    )

    if not symbols:
        return {
            "status": "NO_OPEN_POSITIONS",
            "symbols": [],
            "prices": {},
        }

    quotes = quote_provider(
        symbols
    )

    current_prices = build_current_prices(
        quotes
    )

    if current_prices:
        snapshot_writer(
            current_prices
        )

    return {
        "status": "COMPLETED",
        "symbols": symbols,
        "prices": current_prices,
    }
