"""
Strategy rules for the TSX Momentum Trading backtester.

This file will decide whether a historical setup is READY, WATCH, or IGNORE.
"""


def evaluate_historical_setup(row, previous_row=None):
    """
    Evaluate one historical trading day.

    For Version 2.0, this is a simple placeholder.
    We will later connect this to our real TMQS, RVOL, breakout,
    momentum, liquidity, and decision engine.
    """

    if previous_row is None:
        return {
            "decision": "IGNORE",
            "reason": "No previous day data",
        }

    close = row["close"]
    previous_high = previous_row["high"]
    previous_close = previous_row["close"]
    volume = row["volume"]
    previous_volume = previous_row["volume"]

    rvol = volume / previous_volume if previous_volume > 0 else 0

    if close > previous_high and rvol >= 1.5:
        return {
            "decision": "READY",
            "reason": "Breakout with strong relative volume",
        }

    if close > previous_close and rvol >= 0.75:
        return {
            "decision": "WATCH",
            "reason": "Positive close with acceptable volume",
        }

    return {
        "decision": "IGNORE",
        "reason": "No qualified setup",
    }