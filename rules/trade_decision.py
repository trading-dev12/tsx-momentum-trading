def get_trade_decision(quote):
    """
    Returns WATCH, BUY or IGNORE.
    """

    score = quote["score"]

    if score >= 50:
        return "BUY"

    elif score >= 25:
        return "WATCH"

    else:
        return "IGNORE"