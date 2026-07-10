"""
Live TMQS Scoring

Calculates the live Trading Momentum Quality Score and
provides a transparent breakdown of each scoring component.
"""


def calculate_tmqs_breakdown(quote):
    """
    Calculate the live TMQS score and return a detailed breakdown.

    This preserves the existing scoring rules and hard quality caps.
    """

    base_score = 50

    gap_percent = quote.get("gap_percent", 0)
    rvol = quote.get("relative_volume", 0)
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)

    grades = quote.get("grades", {})
    momentum_grade = grades.get("Momentum", "C")
    liquidity_grade = grades.get("Liquidity", "C")

    gap_score = 0
    rvol_score = 0
    momentum_score = 0
    liquidity_score = 0
    breakout_score = 0
    previous_close_score = 0

    # Gap quality
    if gap_percent >= 2:
        gap_score = 10
    elif gap_percent >= 1:
        gap_score = 5
    elif gap_percent < 0:
        gap_score = -10

    # RVOL quality
    if rvol >= 2.0:
        rvol_score = 20
    elif rvol >= 1.5:
        rvol_score = 12
    elif rvol >= 1.0:
        rvol_score = 5
    elif rvol < 0.5:
        rvol_score = -30
    else:
        rvol_score = -15

    # Momentum quality
    if momentum_grade == "A":
        momentum_score = 15
    elif momentum_grade == "B":
        momentum_score = 8
    elif momentum_grade == "C":
        momentum_score = -5
    else:
        momentum_score = -15

    # Liquidity quality
    if liquidity_grade == "A":
        liquidity_score = 10
    elif liquidity_grade == "B":
        liquidity_score = 5
    elif liquidity_grade == "C":
        liquidity_score = -5
    else:
        liquidity_score = -15

    # Breakout quality
    if previous_high > 0:
        if price >= previous_high:
            breakout_score = 15
        elif price >= previous_high * 0.99:
            breakout_score = 5
        else:
            breakout_score = -10

    # Previous-close quality
    if previous_close > 0:
        if price > previous_close:
            previous_close_score = 5
        else:
            previous_close_score = -10

    raw_score = (
        base_score
        + gap_score
        + rvol_score
        + momentum_score
        + liquidity_score
        + breakout_score
        + previous_close_score
    )

    final_score = raw_score
    applied_caps = []

    # Hard quality caps
    if rvol < 0.5:
        final_score = min(final_score, 45)
        applied_caps.append("RVOL below 0.50 capped TMQS at 45")

    elif rvol < 1.0:
        final_score = min(final_score, 65)
        applied_caps.append("RVOL below 1.00 capped TMQS at 65")

    elif rvol < 1.5:
        final_score = min(final_score, 80)
        applied_caps.append("RVOL below 1.50 capped TMQS at 80")

    if liquidity_grade in ["D", "F"]:
        final_score = min(final_score, 60)
        applied_caps.append(
            "Low liquidity grade capped TMQS at 60"
        )

    if momentum_grade in ["D", "F"]:
        final_score = min(final_score, 55)
        applied_caps.append(
            "Low momentum grade capped TMQS at 55"
        )

    final_score = max(0, min(final_score, 100))

    return {
        "tmqs": final_score,
        "base_score": base_score,
        "gap_score": gap_score,
        "rvol_score": rvol_score,
        "momentum_score": momentum_score,
        "liquidity_score": liquidity_score,
        "breakout_score": breakout_score,
        "previous_close_score": previous_close_score,
        "raw_score": raw_score,
        "applied_caps": applied_caps,
    }


def calculate_tmqs(quote):
    """
    Return only the final live TMQS score.

    Existing code can continue calling this function unchanged.
    """

    breakdown = calculate_tmqs_breakdown(quote)
    return breakdown["tmqs"]