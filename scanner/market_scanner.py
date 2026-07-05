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
    if decision == "BUY":
        return GREEN + decision + RESET

    if decision == "WATCH":
        return YELLOW + decision + RESET

    if decision == "IGNORE":
        return RED + decision + RESET

    return decision


def color_rvol(rvol):
    if rvol >= 2:
        return GREEN + f"{rvol:.2f}x" + RESET

    if rvol >= 1:
        return YELLOW + f"{rvol:.2f}x" + RESET

    return RED + f"{rvol:.2f}x" + RESET


def color_breakout(status):
    short_status = shorten_breakout_status(status)

    if status == "BREAKOUT":
        return GREEN + short_status + RESET

    if status == "NEAR BREAKOUT":
        return YELLOW + short_status + RESET

    if status == "WEAK / BELOW CLOSE":
        return RED + short_status + RESET

    return short_status


def display_market_data(quotes):
    print("=" * 92)
    print("TSX MOMENTUM SCANNER - DASHBOARD")
    print("=" * 92)

    print(
        f"{'Rank':<6}"
        f"{'Symbol':<8}"
        f"{'Price':>10}  "
        f"{'TMQS':>5}  "
        f"{'RVOL':>8}  "
        f"{'Breakout':<12}"
        f"{'Mom':<6}"
        f"{'Liq':<6}"
        f"{'Decision':<10}"
    )

    print("-" * 92)

    for rank, quote in enumerate(quotes, start=1):
        breakout = color_breakout(quote["breakout_status"])
        rvol = color_rvol(quote["relative_volume"])
        decision = color_decision(quote["decision"])

        print(
            f"{rank:<6}"
            f"{quote['symbol']:<8}"
            f"{quote['price']:>10.2f}  "
            f"{quote['tmqs']:>5}  "
            f"{rvol:<8}  "
            f"{breakout:<12}"
            f"{quote['grades']['Momentum']:<6}"
            f"{quote['grades']['Liquidity']:<6}"
            f"{decision:<10}"
        )

    print("=" * 92)