def calculate_confidence_score(quote):
    """
    Calculates an overall confidence score from 0 to 100.
    """

    score = 0

    tmqs = quote.get("tmqs", 0)
    rvol = quote.get("relative_volume", 0)
    breakout = quote.get("breakout_status", "")
    momentum = quote.get("grades", {}).get("Momentum", "C")
    liquidity = quote.get("grades", {}).get("Liquidity", "C")

    # TMQS contribution
    score += tmqs * 0.40

    # RVOL contribution
    if rvol >= 2.0:
        score += 25
    elif rvol >= 1.5:
        score += 20
    elif rvol >= 1.0:
        score += 15
    elif rvol >= 0.75:
        score += 10
    elif rvol >= 0.5:
        score += 5

    # Breakout contribution
    if breakout == "BREAKOUT":
        score += 15
    elif breakout == "NEAR BREAKOUT":
        score += 10
    elif breakout == "INSIDE RANGE":
        score += 5

    # Momentum contribution
    if momentum == "A":
        score += 10
    elif momentum == "B":
        score += 5

    # Liquidity contribution
    if liquidity == "A":
        score += 10
    elif liquidity == "B":
        score += 5

    return round(max(0, min(score, 100)))