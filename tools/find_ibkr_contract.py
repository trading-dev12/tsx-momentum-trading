from ib_insync import IB


ib = IB()

try:
    ib.connect(
        "127.0.0.1",
        7496,
        clientId=12,
        readonly=True,
        timeout=10,
    )

    matches = ib.reqMatchingSymbols("TECK")

    for match in matches:
        contract = match.contract

        print("=" * 70)
        print("Symbol          :", contract.symbol)
        print("Local Symbol    :", contract.localSymbol)
        print("Trading Class   :", contract.tradingClass)
        print("Security Type   :", contract.secType)
        print("Primary Exchange:", contract.primaryExchange)
        print("Currency        :", contract.currency)
        print("Description     :", match.derivativeSecTypes)
        print("ConId           :", contract.conId)

finally:
    ib.disconnect()