def calculate_score(quote):
    """
    Calculates a simple momentum score.
    """

    score = 0

    # Daily price change
    score += quote["change_percent"] * 20

    # Volume bonus
    score += min(quote["volume"] / 100000, 50)

    return round(score, 1)