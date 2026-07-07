def calculate_tmqs(quote):
    score = 50

    gap_percent = quote.get("gap_percent", 0)
    rvol = quote.get("relative_volume", 0)
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)
    momentum_grade = quote.get("grades", {}).get("Momentum", "C")
    liquidity_grade = quote.get("grades", {}).get("Liquidity", "C")

    # Gap quality
    if gap_percent >= 2:
        score += 10
    elif gap_percent >= 1:
        score += 5
    elif gap_percent < 0:
        score -= 10

    # RVOL quality
    if rvol >= 2.0:
        score += 20
    elif rvol >= 1.5:
        score += 12
    elif rvol >= 1.0:
        score += 5
    elif rvol < 0.5:
        score -= 30
    else:
        score -= 15

    # Momentum quality
    if momentum_grade == "A":
        score += 15
    elif momentum_grade == "B":
        score += 8
    elif momentum_grade == "C":
        score -= 5
    else:
        score -= 15

    # Liquidity quality
    if liquidity_grade == "A":
        score += 10
    elif liquidity_grade == "B":
        score += 5
    elif liquidity_grade == "C":
        score -= 5
    else:
        score -= 15

    # Breakout quality
    if previous_high > 0:
        if price >= previous_high:
            score += 15
        elif price >= previous_high * 0.99:
            score += 5
        else:
            score -= 10

    # Previous close quality
    if previous_close > 0:
        if price > previous_close:
            score += 5
        else:
            score -= 10

    # Hard quality caps
    if rvol < 0.5:
        score = min(score, 45)
    elif rvol < 1.0:
        score = min(score, 65)
    elif rvol < 1.5:
        score = min(score, 80)

    if liquidity_grade in ["D", "F"]:
        score = min(score, 60)

    if momentum_grade in ["D", "F"]:
        score = min(score, 55)

    return max(0, min(score, 100))