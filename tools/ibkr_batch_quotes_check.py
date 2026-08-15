from core.ibkr_data_provider import IBKRDataProvider
from core.watchlist_loader import load_all_watchlists


provider = IBKRDataProvider(client_id=13)

try:
    symbols = sorted(load_all_watchlists())

    quotes, errors = provider.get_quotes(symbols)

    print("=" * 70)
    print("IBKR BATCH QUOTE TEST")
    print("=" * 70)
    print(f"Requested : {len(symbols)}")
    print(f"Received  : {len(quotes)}")
    print(f"Errors    : {len(errors)}")

    for symbol in symbols:
        quote = quotes.get(symbol)

        if quote:
            print(
                f"PASS {symbol:<12} "
                f"${quote['price']:<10.2f} "
                f"{quote['price_source']:<8} "
                f"Volume {quote.get('volume')}"
            )
        else:
            print(
                f"FAIL {symbol:<12} "
                f"{errors.get(symbol, 'Unknown error')}"
            )

finally:
    provider.disconnect()