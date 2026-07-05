import yfinance as yf

from core.previous_day import get_previous_day


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

    return {
        "symbol": symbol,
        "price": price,
        "previous_high": previous_high,
        "previous_low": previous_low,
        "previous_close": previous_close,
        "gap_percent": gap_percent,
        "change_percent": change_percent,
        "volume": volume,
        "status": "Live Data"
    }


def get_quotes(watchlist):
    quotes = []

    for symbol in watchlist:
        quotes.append(get_live_quote(symbol))

    return quotes