"""
Northstar Quant
Historical Trade Enrichment Engine
"""

from research.market_regime import (
    calculate_market_regime,
)
from research.moving_average_context import (
    calculate_moving_average_context,
)
from research.gap_analysis import (
    calculate_gap_analysis,
)
from research.relative_strength import (
    calculate_relative_strength,
)
from research.sector_strength import (
    calculate_sector_strength,
)
from research.volatility_regime import (
    calculate_volatility_regime,
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
        "gap_analysis": calculate_gap_analysis(
            symbol=symbol,
            measurement_date=signal_date,
        ),
        "sector_strength": calculate_sector_strength(
            symbol=symbol,
            measurement_date=signal_date,
        ),
         "volatility_regime": calculate_volatility_regime(
            symbol=symbol,
            measurement_date=signal_date,
        ),
    }