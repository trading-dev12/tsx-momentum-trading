"""
Northstar Quant
Market Microstructure Snapshot Research

Normalizes bid, ask, last and spread observations.

Research only. Missing quote data never changes paper-trading
execution, exits, sizing or strategy decisions.
"""

from datetime import datetime

from core.market_hours import (
    TORONTO_TIMEZONE,
)


def _positive_float(value):
    try:
        value = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if value <= 0:
        return None

    return value


def build_market_snapshot(
    prefix,
    quote=None,
    source="",
    captured_at=None,
    error="",
):
    quote = quote or {}

    source_value = str(
        quote.get(
            "data_source",
            quote.get(
                "source",
                source,
            ),
        )
        or source
        or ""
    )

    timestamp = (
        quote.get("quote_timestamp")
        or captured_at
    )

    if not timestamp:
        timestamp = datetime.now(
            TORONTO_TIMEZONE
        ).isoformat(
            timespec="seconds"
        )

    bid = _positive_float(
        quote.get("bid")
    )

    ask = _positive_float(
        quote.get("ask")
    )

    last = _positive_float(
        quote.get(
            "last",
            quote.get("price"),
        )
    )

    midpoint = None
    spread_amount = None
    spread_percent = None

    if (
        bid is not None
        and ask is not None
        and ask >= bid
    ):
        midpoint = (
            bid + ask
        ) / 2

        spread_amount = (
            ask - bid
        )

        if midpoint > 0:
            spread_percent = (
                spread_amount
                / midpoint
                * 100
            )

        status = "AVAILABLE"

    elif (
        bid is not None
        or ask is not None
    ):
        status = "PARTIAL"

    else:
        status = "UNAVAILABLE"

    error_text = str(
        error or ""
    )

    if (
        status == "UNAVAILABLE"
        and not error_text
    ):
        error_text = (
            "Bid/ask snapshot unavailable."
        )

    return {
        f"{prefix}_quote_status": status,
        f"{prefix}_quote_source": source_value,
        f"{prefix}_quote_timestamp": str(
            timestamp
        ),
        f"{prefix}_bid": (
            bid if bid is not None else ""
        ),
        f"{prefix}_ask": (
            ask if ask is not None else ""
        ),
        f"{prefix}_last": (
            last if last is not None else ""
        ),
        f"{prefix}_midpoint": (
            round(midpoint, 6)
            if midpoint is not None
            else ""
        ),
        f"{prefix}_spread_amount": (
            round(spread_amount, 6)
            if spread_amount is not None
            else ""
        ),
        f"{prefix}_spread_percent": (
            round(spread_percent, 6)
            if spread_percent is not None
            else ""
        ),
        f"{prefix}_quote_error": (
            error_text
        ),
    }


def copy_market_snapshot(
    prefix,
    payload,
):
    payload = payload or {}

    suffixes = [
        "quote_status",
        "quote_source",
        "quote_timestamp",
        "bid",
        "ask",
        "last",
        "midpoint",
        "spread_amount",
        "spread_percent",
        "quote_error",
    ]

    result = {}

    for suffix in suffixes:
        field = f"{prefix}_{suffix}"

        if field in payload:
            result[field] = payload[field]

    return result
