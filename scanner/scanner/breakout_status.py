def get_breakout_status(quote):
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)

    if price <= 0 or previous_high <= 0 or previous_close <= 0:
        return "UNKNOWN"

    if price > previous_high:
        return "BREAKOUT"

    if price >= previous_high * 0.995:
        return "NEAR BREAKOUT"

    if price >= previous_close:
        return "INSIDE RANGE"

    return "WEAK / BELOW CLOSE"