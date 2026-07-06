def calculate_tmqs(quote):

    score = 0

    gap_percent = quote.get("gap_percent", 0)
    rvol = quote.get("relative_volume", 0)
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)
    momentum_grade = quote.get("grades", {}).get("Momentum", "C")
    liquidity_grade = quote.get("grades", {}).get("Liquidity", "C")

    # Gap score
    if gap_percent >= 2:
        score += 15
    elif gap_percent >= 1:
        score += 10
    elif gap_percent > 0:
        score += 5

    # Momentum grade
    if momentum_grade == "A":
        score += 25
    elif momentum_grade == "B":
        score += 15
    elif momentum_grade == "C":
        score += 5

    # Liquidity grade
    if liquidity_grade == "A":
        score += 20
    elif liquidity_grade == "B":
        score += 12
    elif liquidity_grade == "C":
        score += 5

    # Relative volume score
    if rvol >= 2.0:
        score += 25
    elif rvol >= 1.5:
        score += 20
    elif rvol >= 1.0:
        score += 15
    elif rvol >= 0.5:
        score += 5
    elif rvol < 0.3:
        score -= 15
    else:
        score -= 8

    # Price near or above previous high
    if previous_high > 0:
        if price >= previous_high:
            score += 20
        elif price >= previous_high * 0.99:
            score += 10

    # Price above previous close
    if previous_close > 0 and price > previous_close:
        score += 10

    # RVOL quality cap
    if rvol < 0.5:
        score = min(score, 60)
    elif rvol < 1.0:
        score = min(score, 75)
    elif rvol < 1.5:
        score = min(score, 85)

    return max(0, min(score, 100))