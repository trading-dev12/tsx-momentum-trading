def get_trade_decision(quote):
    """
    Determines whether a stock is READY, WATCH, or IGNORE.
    """

    tmqs = quote["tmqs"]
    rvol = quote["relative_volume"]
    breakout = quote["breakout_status"]
    momentum = quote["grades"]["Momentum"]
    liquidity = quote["grades"]["Liquidity"]

    # READY
    if (
        tmqs >= 80
        and rvol >= 1.5
        and breakout in ["BREAKOUT", "NEAR BREAKOUT"]
        and momentum in ["A", "B"]
        and liquidity in ["A", "B"]
    ):
        return "READY"

    # WATCH
    if (
        tmqs >= 60
        and breakout in ["BREAKOUT", "NEAR BREAKOUT", "INSIDE RANGE"]
    ):
        return "WATCH"

    # IGNORE
    return "IGNORE"