def make_trade_decision(quote):
    score = quote["score"]
    gap = quote["gap_percent"]
    momentum = quote["grades"]["Momentum"]
    liquidity = quote["grades"]["Liquidity"]

    if score >= 50 and gap >= 2 and momentum == "A" and liquidity == "A":
        return "TRADE READY"

    if score >= 30 and gap > 0 and liquidity in ["A", "B"]:
        return "WATCH"

    return "IGNORE"