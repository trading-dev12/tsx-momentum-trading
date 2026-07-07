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

    score = 50

    if close > previous_high:
        breakout = "BREAKOUT"
        score += 15
    elif close >= previous_high * 0.995:
        breakout = "NEAR BREAKOUT"
        score += 5
    elif close >= previous_close:
        breakout = "INSIDE RANGE"
        score -= 5
    else:
        breakout = "WEAK / BELOW CLOSE"
        score -= 20

    if rvol >= 2.5:
        score += 25
    elif rvol >= 2.0:
        score += 20
    elif rvol >= 1.5:
        score += 12
    elif rvol >= 1.0:
        score += 5
    elif rvol < 0.5:
        score -= 30
    else:
        score -= 15

    if close > previous_close:
        score += 5
    else:
        score -= 10

    if rvol < 0.5:
        score = min(score, 45)
    elif rvol < 1.0:
        score = min(score, 65)
    elif rvol < 1.5:
        score = min(score, 80)

    tmqs = max(0, min(score, 100))

    if tmqs >= 80 and breakout == "BREAKOUT" and rvol >= 1.5:
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