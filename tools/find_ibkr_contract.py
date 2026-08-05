from ib_insync import IB


SEARCH_SYMBOLS = [
    "CCL",
    "EMP",
    "GIB",
]


ib = IB()

try:
    ib.connect(
        "127.0.0.1",
        7496,
        clientId=12,
        readonly=True,
        timeout=10,
    )

    for search_symbol in SEARCH_SYMBOLS:
        print()
        print("#" * 72)
        print(f"SEARCH: {search_symbol}")
        print("#" * 72)

        matches = ib.reqMatchingSymbols(search_symbol)

        for match in matches:
            contract = match.contract

            if (
                contract.secType == "STK"
                and contract.primaryExchange == "TSE"
                and contract.currency == "CAD"
            ):
                print("=" * 70)
                print("Symbol          :", contract.symbol)
                print("Local Symbol    :", contract.localSymbol)
                print("Trading Class   :", contract.tradingClass)
                print("Primary Exchange:", contract.primaryExchange)
                print("Currency        :", contract.currency)
                print("ConId           :", contract.conId)

finally:
    ib.disconnect()