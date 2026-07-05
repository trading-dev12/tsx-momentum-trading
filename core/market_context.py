import yfinance as yf


MARKET_SYMBOLS = {
    "tsx": "^GSPTSE",
    "oil": "CL=F",
    "bitcoin": "BTC-CAD",
    "vix": "^VIX",
}


def get_symbol_change(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")

        if hist.empty or len(hist) < 2:
            return None

        previous_close = hist["Close"].iloc[-2]
        current_price = hist["Close"].iloc[-1]

        change_percent = ((current_price - previous_close) / previous_close) * 100
        return round(change_percent, 2)

    except Exception:
        return None


def score_market_context():
    tsx_change = get_symbol_change(MARKET_SYMBOLS["tsx"])
    oil_change = get_symbol_change(MARKET_SYMBOLS["oil"])
    bitcoin_change = get_symbol_change(MARKET_SYMBOLS["bitcoin"])
    vix_change = get_symbol_change(MARKET_SYMBOLS["vix"])

    score = 0
    notes = []

    if tsx_change is not None:
        if tsx_change > 0.4:
            score += 30
            notes.append("TSX strong")
        elif tsx_change > 0:
            score += 20
            notes.append("TSX positive")
        elif tsx_change > -0.5:
            score += 10
            notes.append("TSX weak")
        else:
            notes.append("TSX bearish")

    if oil_change is not None:
        if oil_change > 1:
            score += 20
            notes.append("Oil strong")
        elif oil_change > 0:
            score += 10
            notes.append("Oil positive")
        else:
            notes.append("Oil weak")

    if bitcoin_change is not None:
        if bitcoin_change > 2:
            score += 20
            notes.append("Bitcoin strong")
        elif bitcoin_change > 0:
            score += 10
            notes.append("Bitcoin positive")
        else:
            notes.append("Bitcoin weak")

    if vix_change is not None:
        if vix_change < -2:
            score += 20
            notes.append("VIX falling")
        elif vix_change < 0:
            score += 10
            notes.append("VIX slightly lower")
        elif vix_change > 5:
            score -= 20
            notes.append("VIX spike warning")
        else:
            notes.append("VIX stable")

    if score >= 70:
        status = "STRONG"
    elif score >= 45:
        status = "NEUTRAL"
    else:
        status = "WEAK"

    return {
        "score": score,
        "status": status,
        "tsx_change": tsx_change,
        "oil_change": oil_change,
        "bitcoin_change": bitcoin_change,
        "vix_change": vix_change,
        "notes": notes,
    }