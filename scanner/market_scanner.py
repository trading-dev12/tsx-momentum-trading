GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def shorten_breakout_status(status):
    if status == "BREAKOUT":
        return "Breakout"
    if status == "NEAR BREAKOUT":
        return "Near BO"
    if status == "INSIDE RANGE":
        return "Inside"
    if status == "WEAK / BELOW CLOSE":
        return "Weak"
    return "Unknown"


def color_decision(decision):
    if decision == "READY":
        return GREEN + decision + RESET
    if decision == "BUY":
        return GREEN + decision + RESET
    if decision == "WATCH":
        return YELLOW + decision + RESET
    if decision == "IGNORE":
        return RED + decision + RESET
    return decision


def display_market_data(quotes):
    print("=" * 82)
    print("TSX MOMENTUM SCANNER - DASHBOARD")
    print("=" * 82)

    print(
        f"{'#':<4}"
        f"{'Symbol':<8}"
        f"{'Price':>10}"
        f"{'TMQS':>8}"
        f"{'RVOL':>8}"
        f"{'Breakout':>14}"
        f"{'Grade':>10}"
        f"{'Decision':>12}"
    )

    print("-" * 82)

    for rank, quote in enumerate(quotes, start=1):
        symbol = quote["symbol"]
        price = quote["price"]
        tmqs = quote["tmqs"]
        rvol = quote["relative_volume"]
        breakout = shorten_breakout_status(quote["breakout_status"])
        momentum_grade = quote["grades"]["Momentum"]
        liquidity_grade = quote["grades"]["Liquidity"]
        decision = quote["decision"]

        plain_row = (
            f"{rank:<4}"
            f"{symbol:<8}"
            f"{price:>10.2f}"
            f"{tmqs:>8}"
            f"{rvol:>7.2f}x"
            f"{breakout:>14}"
            f"{momentum_grade + '/' + liquidity_grade:>10}"
            f"{decision:>12}"
        )

        colored_decision = color_decision(decision)
        row_without_decision = plain_row[:-12]

        print(row_without_decision + f"{colored_decision:>12}")

    print("=" * 82)