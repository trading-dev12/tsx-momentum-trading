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

    breakout_score = 0
    volume_score = 0
    price_score = 0

    # Breakout quality - max 35 points
    breakout_percent = ((close - previous_high) / previous_high) * 100

    if breakout_percent >= 2.0:
        breakout = "STRONG BREAKOUT"
        breakout_score = 35
    elif breakout_percent >= 1.0:
        breakout = "STRONG BREAKOUT"
        breakout_score = 30
    elif breakout_percent > 0:
        breakout = "BREAKOUT"
        breakout_score = 24 + min(breakout_percent * 6, 6)
    elif breakout_percent >= -0.5:
        breakout = "NEAR BREAKOUT"
        breakout_score = 16
    elif close >= previous_close:
        breakout = "INSIDE RANGE"
        breakout_score = 8
    else:
        breakout = "WEAK / BELOW CLOSE"
        breakout_score = 0

    # Relative volume quality - max 35 points
    if rvol >= 3.0:
        volume_score = 35
    elif rvol >= 2.5:
        volume_score = 30 + ((rvol - 2.5) / 0.5) * 5
    elif rvol >= 2.0:
        volume_score = 24 + ((rvol - 2.0) / 0.5) * 6
    elif rvol >= 1.5:
        volume_score = 16 + ((rvol - 1.5) / 0.5) * 8
    elif rvol >= 1.0:
        volume_score = 8 + ((rvol - 1.0) / 0.5) * 8
    elif rvol >= 0.75:
        volume_score = 4
    else:
        volume_score = 0

    # Daily price strength - max 30 points
    price_change_percent = ((close - previous_close) / previous_close) * 100

    if price_change_percent >= 4.0:
        price_score = 30
    elif price_change_percent >= 2.0:
        price_score = 20 + ((price_change_percent - 2.0) / 2.0) * 10
    elif price_change_percent > 0:
        price_score = 10 + (price_change_percent / 2.0) * 10
    else:
        price_score = 0

    score = breakout_score + volume_score + price_score

    # Quality caps
    if rvol < 0.75:
        score = min(score, 45)
    elif rvol < 1.0:
        score = min(score, 55)
    elif rvol < 1.5:
        score = min(score, 70)

    if breakout in ["WEAK / BELOW CLOSE", "INSIDE RANGE"]:
        score = min(score, 55)

    if breakout == "NEAR BREAKOUT":
        score = min(score, 75)

    tmqs = round(max(0, min(score, 100)), 2)

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

        # TMQS Breakdown
        "breakout_score": round(breakout_score, 2),
        "volume_score": round(volume_score, 2),
        "price_score": round(price_score, 2),
    }