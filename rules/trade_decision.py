def get_trade_decision(quote):
    """
    Returns a clean decision and reason.
    """

    tmqs = quote["tmqs"]
    rvol = quote["relative_volume"]
    breakout = quote["breakout_status"]
    momentum = quote["grades"]["Momentum"]
    liquidity = quote["grades"]["Liquidity"]

    if (
        tmqs >= 80
        and rvol >= 1.5
        and breakout in ["BREAKOUT", "NEAR BREAKOUT"]
        and momentum in ["A", "B"]
        and liquidity in ["A", "B"]
    ):
        return "READY", "All rules passed"

    if (
        tmqs >= 60
        and rvol >= 0.75
        and breakout in ["BREAKOUT", "NEAR BREAKOUT", "INSIDE RANGE"]
        and momentum in ["A", "B"]
        and liquidity in ["A", "B"]
    ):
        return "WATCH", "Waiting for confirmation"

    if rvol < 0.75:
        return "IGNORE", "RVOL too low"

    if momentum == "C":
        return "IGNORE", "Weak momentum"

    if liquidity == "C":
        return "IGNORE", "Low liquidity"

    if breakout == "WEAK / BELOW CLOSE":
        return "IGNORE", "Below previous close"

    return "IGNORE", "Low TMQS"