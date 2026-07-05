import yfinance as yf


def get_previous_day(symbol):

    ticker = yf.Ticker(symbol + ".TO")

    history = ticker.history(period="5d")

    if len(history) < 2:
        return None

    previous = history.iloc[-2]

    return {
        "previous_high": round(previous["High"], 2),
        "previous_low": round(previous["Low"], 2),
        "previous_close": round(previous["Close"], 2)
    }


if __name__ == "__main__":

    data = get_previous_day("SHOP")

    print(data)