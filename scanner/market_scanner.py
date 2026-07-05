GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def shorten_breakout_status(status):
    if status == "BREAKOUT":
        return "Breakout"
    elif status == "NEAR BREAKOUT":
        return "Near BO"
    elif status == "INSIDE RANGE":
        return "Inside"
    elif status == "WEAK / BELOW CLOSE":
        return "Weak"
    return "Unknown"


def color_decision(decision):
    if decision in ("READY", "BUY"):
        return GREEN + decision + RESET
    elif decision == "WATCH":
        return YELLOW + decision + RESET
    elif decision == "IGNORE":
        return RED + decision + RESET
    return decision


def display_scanner_summary(quotes):
    total = len(quotes)

    ready = sum(1 for q in quotes if q["decision"] == "READY")
    buy = sum(1 for q in quotes if q["decision"] == "BUY")
    watch = sum(1 for q in quotes if q["decision"] == "WATCH")
    ignore = sum(1 for q in quotes if q["decision"] == "IGNORE")

    avg_tmqs = sum(q["tmqs"] for q in quotes) / total if total else 0
    best = max(quotes, key=lambda q: q["tmqs"]) if total else None

    print()
    print("=" * 100)
    print("SCANNER SUMMARY")
    print("=" * 100)
    print(f"Stocks Scanned : {total}")
    print(f"READY          : {ready}")
    print(f"BUY            : {buy}")
    print(f"WATCH          : {watch}")
    print(f"IGNORE         : {ignore}")
    print(f"Average TMQS   : {avg_tmqs:.1f}")

    if best:
        print(f"Best Candidate : {best['symbol']} (TMQS {best['tmqs']})")

    print("=" * 100)
    print()


def display_market_data(quotes):
    display_scanner_summary(quotes)

    print("=" * 100)
    print("TSX MOMENTUM TRADING WORKSTATION")
    print("=" * 100)

    print(
        f"{'#':<4}"
        f"{'Symbol':<8}"
        f"{'Price':>10}"
        f"{'TMQS':>8}"
        f"{'RVOL':>8}"
        f"{'Breakout':>14}"
        f"{'Mom':>8}"
        f"{'Liq':>8}"
        f"{'Decision':>14}"
    )

    print("-" * 100)

    for rank, quote in enumerate(quotes, start=1):
        symbol = quote["symbol"]
        price = quote["price"]
        tmqs = quote["tmqs"]
        rvol = quote["relative_volume"]
        breakout = shorten_breakout_status(quote["breakout_status"])
        momentum = quote["grades"]["Momentum"]
        liquidity = quote["grades"]["Liquidity"]
        decision = color_decision(quote["decision"])

        print(
            f"{rank:<4}"
            f"{symbol:<8}"
            f"{price:>10.2f}"
            f"{tmqs:>8}"
            f"{rvol:>7.2f}x"
            f"{breakout:>14}"
            f"{momentum:>8}"
            f"{liquidity:>8}"
            f"{decision:>14}"
        )

    print("=" * 100)