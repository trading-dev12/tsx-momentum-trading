import yfinance as yf

from core.previous_day import get_previous_day
from scanner.momentum_score import calculate_score
from scanner.stock_grader import grade_stock
from scanner.tmqs_score import calculate_tmqs
from rules.trade_decision import get_trade_decision


def get_breakout_status(quote):
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)

    if price <= 0 or previous_high <= 0 or previous_close <= 0:
        return "UNKNOWN"

    if price > previous_high:
        return "BREAKOUT"

    if price >= previous_high * 0.995:
        return "NEAR BREAKOUT"

    if price >= previous_close:
        return "INSIDE RANGE"

    return "WEAK / BELOW CLOSE"


def get_live_quote(symbol):
    ticker = yf.Ticker(symbol + ".TO")
    info = ticker.fast_info

    price = info.get("lastPrice", 0)
    volume = info.get("lastVolume", 0)

    previous_day = get_previous_day(symbol)

    if previous_day:
        previous_close = previous_day["previous_close"]
        previous_high = previous_day["previous_high"]
        previous_low = previous_day["previous_low"]
    else:
        previous_close = 0
        previous_high = 0
        previous_low = 0

    if previous_close:
        change_percent = ((price - previous_close) / previous_close) * 100
        gap_percent = change_percent
    else:
        change_percent = 0
        gap_percent = 0

    quote = {
        "symbol": symbol,
        "price": price,
        "previous_high": previous_high,
        "previous_low": previous_low,
        "previous_close": previous_close,
        "gap_percent": gap_percent,
        "change_percent": change_percent,
        "volume": volume,
        "status": "Live Data",
    }

    quote["score"] = calculate_score(quote)
    quote["grades"] = grade_stock(quote)
    quote["tmqs"] = calculate_tmqs(quote)
    quote["breakout_status"] = get_breakout_status(quote)
    quote["decision"] = get_trade_decision(quote)

    return quote


def get_quotes(watchlist):
    quotes = []

    for symbol in watchlist:
        quotes.append(get_live_quote(symbol))

    quotes.sort(key=lambda quote: quote["tmqs"], reverse=True)

    return quotes