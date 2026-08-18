"""
Northstar Quant
On-Demand Stock Research

Read-only analysis for an arbitrary TSX-listed stock.

This module does not:
- modify any strategy
- add symbols to a watchlist
- create signals
- create pending trades
- create positions
- modify the 200-trade validation sample
"""

from __future__ import annotations

from datetime import date

from core.ibkr_data_provider import (
    IBKRDataProvider,
)
from research.market_regime import (
    calculate_market_regime,
)
from research.moving_average_context import (
    calculate_moving_average_context,
)
from research.relative_strength import (
    calculate_relative_strength,
)
from research.volatility_regime import (
    calculate_volatility_regime,
)


STOCK_RESEARCH_IBKR_CLIENT_ID = 30


def normalize_tsx_symbol(symbol):
    """
    Normalize user input into Northstar/Yahoo TSX notation.

    Examples:
        DOL      -> DOL.TO
        dol.to   -> DOL.TO
        TECK-B   -> TECK-B.TO
    """

    normalized = str(
        symbol or ""
    ).strip().upper()

    normalized = normalized.replace(
        " ",
        "",
    )

    if not normalized:
        raise ValueError(
            "A TSX ticker is required."
        )

    if normalized.endswith(
        ".TO"
    ):
        return normalized

    return (
        f"{normalized}.TO"
    )


def load_live_quote(symbol):
    """
    Retrieve an observational IBKR quote.

    A dedicated client ID keeps on-demand research separate
    from Northstar's trading/scanner connections.
    """

    provider = IBKRDataProvider(
        client_id=(
            STOCK_RESEARCH_IBKR_CLIENT_ID
        )
    )

    try:
        result = provider.get_quote(
            symbol
        )

        result = dict(
            result
        )

        result["status"] = (
            "AVAILABLE"
        )

        result.setdefault(
            "reason",
            "",
        )

        return result

    finally:
        provider.disconnect()


def _run_component(
    component_name,
    function,
    *args,
):
    """
    Run one research component fail-soft.

    One unavailable provider must not prevent the remaining
    stock research from being displayed.
    """

    try:
        result = function(
            *args
        )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                f"{component_name} returned "
                "a non-dictionary result."
            )

        normalized = dict(
            result
        )

        normalized.setdefault(
            "status",
            "AVAILABLE",
        )

        normalized.setdefault(
            "reason",
            "",
        )

        return normalized

    except Exception as error:
        return {
            "status": "UNAVAILABLE",
            "reason": str(
                error
            ),
        }


def build_stock_research_report(
    symbol,
    measurement_date=None,
    quote_provider=load_live_quote,
    market_regime_provider=(
        calculate_market_regime
    ),
    relative_strength_provider=(
        calculate_relative_strength
    ),
    moving_average_provider=(
        calculate_moving_average_context
    ),
    volatility_provider=(
        calculate_volatility_regime
    ),
):
    """
    Build one read-only Northstar research report.

    This is deliberately independent of the three strategy
    execution pipelines.
    """

    normalized_symbol = (
        normalize_tsx_symbol(
            symbol
        )
    )

    if measurement_date is None:
        measurement_date = (
            date.today().isoformat()
        )
    else:
        measurement_date = str(
            measurement_date
        ).strip()

    quote = _run_component(
        "IBKR quote",
        quote_provider,
        normalized_symbol,
    )

    market_regime = _run_component(
        "Market regime",
        market_regime_provider,
        measurement_date,
    )

    relative_strength = _run_component(
        "Relative strength",
        relative_strength_provider,
        normalized_symbol,
        measurement_date,
    )

    moving_average = _run_component(
        "Moving average context",
        moving_average_provider,
        normalized_symbol,
        measurement_date,
    )

    volatility = _run_component(
        "Volatility regime",
        volatility_provider,
        normalized_symbol,
        measurement_date,
    )

    components = {
        "quote": quote,
        "market_regime": (
            market_regime
        ),
        "relative_strength": (
            relative_strength
        ),
        "moving_average": (
            moving_average
        ),
        "volatility": volatility,
    }

    available_count = sum(
        1
        for result
        in components.values()
        if str(
            result.get(
                "status",
                "",
            )
        ).upper()
        == "AVAILABLE"
    )

    if (
        available_count
        == len(components)
    ):
        overall_status = (
            "COMPLETE"
        )

    elif available_count:
        overall_status = (
            "PARTIAL"
        )

    else:
        overall_status = (
            "UNAVAILABLE"
        )

    unavailable_components = {
        name: result.get(
            "reason",
            "",
        )
        for (
            name,
            result,
        ) in components.items()
        if str(
            result.get(
                "status",
                "",
            )
        ).upper()
        != "AVAILABLE"
    }

    return {
        "mode": (
            "READ_ONLY_STOCK_RESEARCH"
        ),
        "read_only": True,
        "symbol": (
            normalized_symbol
        ),
        "measurement_date": (
            measurement_date
        ),
        "status": overall_status,
        "available_components": (
            available_count
        ),
        "total_components": len(
            components
        ),
        "unavailable_components": (
            unavailable_components
        ),
        **components,
    }
