def calculate_tmqs(quote):

    score = 0

    # Positive gap
    if quote["gap_percent"] > 0:
        score += 10

    # Strong gap
    if quote["gap_percent"] >= 1:
        score += 10

    # Momentum grade
    if quote["grades"]["Momentum"] == "A":
        score += 20
    elif quote["grades"]["Momentum"] == "B":
        score += 10

    # Liquidity grade
    if quote["grades"]["Liquidity"] == "A":
        score += 20
    elif quote["grades"]["Liquidity"] == "B":
        score += 10

    # Price near or above previous high
    if quote["price"] >= quote["previous_high"]:
        score += 20
    elif quote["price"] >= quote["previous_high"] * 0.99:
        score += 10

    # Price above previous close
    if quote["price"] > quote["previous_close"]:
        score += 20

    return min(score, 100)