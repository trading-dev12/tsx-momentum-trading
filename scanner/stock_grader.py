def grade_stock(quote):

    grades = {}

    # Price movement

    if quote["change_percent"] >= 2:
        grades["Momentum"] = "A"

    elif quote["change_percent"] >= 1:
        grades["Momentum"] = "B"

    else:
        grades["Momentum"] = "C"

    # Volume

    if quote["volume"] >= 1000000:
        grades["Liquidity"] = "A"

    elif quote["volume"] >= 500000:
        grades["Liquidity"] = "B"

    else:
        grades["Liquidity"] = "C"

    return grades