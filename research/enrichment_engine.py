"""
Northstar Quant
Historical Trade Enrichment Engine
"""

from research.market_regime import (
    calculate_market_regime,
)
from research.relative_strength import (
    calculate_relative_strength,
)
from research.moving_average_context import (
    calculate_moving_average_context,
)

def enrich_trade(signal):
    """
    Return research metadata attached to every trade.

    Research factors are measured using the signal date so that
    entry-day or future information cannot leak into the results.
    """

    symbol = signal.get("symbol")
    signal_date = signal.get("signal_date")

    return {
        "relative_strength": calculate_relative_strength(
            symbol=symbol,
            measurement_date=signal_date,
        ),
        "market_regime": calculate_market_regime(
            measurement_date=signal_date,
        ),
         "moving_average_context": calculate_moving_average_context(
            symbol=symbol,
            measurement_date=signal_date,
         ),    
   }