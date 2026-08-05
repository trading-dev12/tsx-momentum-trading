from ib_insync import *

ib = IB()

print("Connecting to TWS...")

ib.connect(
    "127.0.0.1",
    7496,
    clientId=1,
    readonly=True,
)

print("Connected:", ib.isConnected())

contract = Stock(
    "ENB",
    "SMART",
    "CAD",
    primaryExchange="TSE",
)

ib.qualifyContracts(contract)

ticker = ib.reqMktData(contract)

ib.sleep(3)

print()
print("========== MARKET DATA ==========")
print("Symbol :", contract.symbol)
print("Last   :", ticker.last)
print("Market :", ticker.marketPrice())
print("Bid    :", ticker.bid)
print("Ask    :", ticker.ask)
print("Close  :", ticker.close)
print("Volume :", ticker.volume)

ib.disconnect()

print()
print("Disconnected.")