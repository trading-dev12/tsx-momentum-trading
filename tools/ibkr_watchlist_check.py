from core.watchlist_loader import load_all_watchlists
from core.ibkr_data_provider import IBKRDataProvider

provider = IBKRDataProvider()

try:
    provider.connect()

    watchlist = sorted(load_all_watchlists())

    print("=" * 70)
    print(f"Testing {len(watchlist)} TSX symbols")
    print("=" * 70)

    passed = []
    failed = []

    for symbol in watchlist:

        try:
            contract = provider.build_tsx_contract(symbol)

            qualified = provider.ib.qualifyContracts(contract)

            if qualified:
                print(f"PASS   {symbol:<12} -> {contract.symbol}")
                passed.append(symbol)
            else:
                print(f"FAIL   {symbol}")
                failed.append(symbol)

        except Exception as error:
            print(f"FAIL   {symbol}   ({error})")
            failed.append(symbol)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Passed : {len(passed)}")
    print(f"Failed : {len(failed)}")

    if failed:
        print()
        print("Needs aliases:")
        for symbol in failed:
            print(symbol)

finally:
    provider.disconnect()