"""
Adapter between the shared market-data quote and the mean reversion strategy.
"""

from strategies.mean_reversion_strategy import MeanReversionInput


def build_mean_reversion_input(quote: dict) -> MeanReversionInput:
    """
    Convert the shared market-data quote dictionary into the typed input
    required by MeanReversionStrategy.
    """

    return MeanReversionInput(
        close=float(quote.get("price", 0) or 0),
        sma20=float(quote.get("sma_20", 0) or 0),
        rsi2=float(quote.get("rsi_2", 0) or 0),
        rsi14=float(quote.get("rsi_14", 0) or 0),
        lower_band=float(
            quote.get("bollinger_lower", 0) or 0
        ),
    )