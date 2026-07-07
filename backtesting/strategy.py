"""
Strategy rules for the TSX Momentum Trading backtester.
"""


def evaluate_historical_setup(row, previous_row=None):
    if previous_row is None:
        return {
            "decision": "IGNORE",
            "reason": "No previous day data",
            "tmqs": 0,
            "rvol": 0,
            "breakout": "UNKNOWN",
        }

    close = row["close"]
    previous_high = previous_row["high"]
    previous_close = previous_row["close"]
    volume = row["volume"]
    previous_volume = previous_row["volume"]

    rvol = volume / previous_volume if previous_volume > 0 else 0

    if close > previous_high:
        breakout = "BREAKOUT"
    elif close >= previous_high * 0.995:
        breakout = "NEAR BREAKOUT"
    elif close >= previous_close:
        breakout = "INSIDE RANGE"
    else:
        breakout = "WEAK / BELOW CLOSE"

    tmqs = 0

    if breakout == "BREAKOUT":
        tmqs += 40
    elif breakout == "NEAR BREAKOUT":
        tmqs += 25
    elif breakout == "INSIDE RANGE":
        tmqs += 10

    if rvol >= 2:
        tmqs += 40
    elif rvol >= 1.5:
        tmqs += 30
    elif rvol >= 1:
        tmqs += 15
    elif rvol >= 0.75:
        tmqs += 5

    if close > previous_close:
        tmqs += 20

    tmqs = min(tmqs, 100)

    if tmqs >= 70 and breakout == "BREAKOUT" and rvol >= 1.5:
        decision = "READY"
        reason = "Strong breakout with volume"
    elif tmqs >= 50 and rvol >= 1:
        decision = "WATCH"
        reason = "Developing setup"
    else:
        decision = "IGNORE"
        reason = "No qualified setup"

    return {
        "decision": decision,
        "reason": reason,
        "tmqs": tmqs,
        "rvol": rvol,
        "breakout": breakout,
    }