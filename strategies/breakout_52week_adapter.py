"""Adapter between the shared market-data quote and the 52-week strategy."""

from strategies.breakout_52week_strategy import Breakout52WeekInput


def build_breakout_52week_input(quote: dict) -> Breakout52WeekInput:
    """
    Convert the shared market-data quote dictionary into the typed input
    required by Breakout52WeekStrategy.
    """

    return Breakout52WeekInput(
        symbol=str(quote.get("symbol", "")),
        close=float(quote.get("price", 0) or 0),
        prior_52_week_high=float(
            quote.get("prior_52_week_high", 0) or 0
        ),
        average_volume=int(quote.get("average_volume", 0) or 0),
        rvol=float(quote.get("relative_volume", 0) or 0),
        sma_50=float(quote.get("sma_50", 0) or 0),
        sma_200=float(quote.get("sma_200", 0) or 0),
    )