"""
Northstar Headless Position Monitor

Provides one headless position-monitoring cycle for the
paper-trading strategies.

IMPORTANT:
Importing this module does NOT fetch market data,
monitor positions, or modify portfolio state.
"""

from datetime import datetime

from core.market_data import get_quotes


def collect_open_position_symbols(engines):
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


def run_headless_position_monitor_cycle(
    engines,
    quote_provider=get_quotes,
    current_date=None,
):
    """
    Run one position-monitoring cycle across all headless
    paper engines.
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

    quotes = quote_provider(symbols)

    current_prices = build_current_prices(
        quotes
    )

    if current_date is None:
        current_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

    closed_trades = {}

    for strategy_name, engine in engines.items():
        closed_trades[strategy_name] = (
            engine.update_positions(
                latest_prices=current_prices,
                current_date=current_date,
            )
        )

    closed_total = sum(
        len(trades)
        for trades in closed_trades.values()
    )

    return {
        "status": "COMPLETED",
        "symbols": symbols,
        "prices": current_prices,
        "closed_trades": closed_trades,
        "closed_total": closed_total,
    }
