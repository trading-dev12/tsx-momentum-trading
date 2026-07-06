def grade_stock(quote):

    grades = {}

    # Price movement
    if quote["change_percent"] >= 2:
        grades["Momentum"] = "A"
    elif quote["change_percent"] >= 1:
        grades["Momentum"] = "B"
    else:
        grades["Momentum"] = "C"

    # Liquidity
    if quote["volume"] >= 1000000:
        grades["Liquidity"] = "A"
    elif quote["volume"] >= 500000:
        grades["Liquidity"] = "B"
    else:
        grades["Liquidity"] = "C"

    # Relative Volume
    rvol = quote.get("relative_volume", 0)

    if rvol >= 2.0:
        grades["RVOL"] = "A"
    elif rvol >= 1.0:
        grades["RVOL"] = "B"
    elif rvol >= 0.5:
        grades["RVOL"] = "C"
    elif rvol >= 0.25:
        grades["RVOL"] = "D"
    else:
        grades["RVOL"] = "F"

    return grades