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

    score = 0

    # Breakout quality
    if close > previous_high * 1.01:
        breakout = "STRONG BREAKOUT"
        score += 40
    elif close > previous_high:
        breakout = "BREAKOUT"
        score += 30
    elif close >= previous_high * 0.995:
        breakout = "NEAR BREAKOUT"
        score += 18
    elif close >= previous_close:
        breakout = "INSIDE RANGE"
        score += 8
    else:
        breakout = "WEAK / BELOW CLOSE"
        score -= 20

    # Relative volume quality
    if rvol >= 3.0:
        score += 35
    elif rvol >= 2.5:
        score += 30
    elif rvol >= 2.0:
        score += 24
    elif rvol >= 1.5:
        score += 16
    elif rvol >= 1.0:
        score += 8
    elif rvol >= 0.75:
        score -= 10
    elif rvol >= 0.5:
        score -= 20
    else:
        score -= 35

    # Daily direction confirmation
    if close > previous_close * 1.02:
        score += 20
    elif close > previous_close:
        score += 10
    else:
        score -= 15

    # Quality caps
    if rvol < 0.5:
        score = min(score, 35)
    elif rvol < 1.0:
        score = min(score, 55)
    elif rvol < 1.5:
        score = min(score, 70)

    if breakout in ["WEAK / BELOW CLOSE", "INSIDE RANGE"]:
        score = min(score, 55)

    if breakout == "NEAR BREAKOUT":
        score = min(score, 75)

    tmqs = max(0, min(score, 100))

    if tmqs >= 80 and breakout in ["BREAKOUT", "STRONG BREAKOUT"] and rvol >= 1.5:
        decision = "READY"
        reason = "Strong breakout with quality volume"
    elif tmqs >= 60 and rvol >= 1.0:
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