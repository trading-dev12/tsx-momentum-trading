def get_mock_quote(symbol):
    """
    Returns simulated market data.
    Later this will be replaced with live TSX data.
    """

    return {
        "symbol": symbol,
        "price": 0.00,
        "volume": 0,
        "status": "Mock Data"
    }


def get_quotes(watchlist):
    quotes = []

    for symbol in watchlist:
        quotes.append(get_mock_quote(symbol))

    return quotes