from pprint import pprint

from core.ibkr_data_provider import get_ibkr_quote


symbols = [
    "ENB.TO",
    "RY.TO",
    "SU.TO",
    "SHOP.TO",
    "TECK-B.TO",
]

for symbol in symbols:
    print()
    print("=" * 60)
    print(f"IBKR QUOTE: {symbol}")
    print("=" * 60)

    try:
        quote = get_ibkr_quote(symbol)
        pprint(quote)

    except Exception as error:
        print(f"FAILED: {error}")