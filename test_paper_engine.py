from paper_trading.paper_engine import PaperTradingEngine


engine = PaperTradingEngine(starting_cash=10000)

signal = {
    "symbol": "HIVE.TO",
    "price": 5.00,
    "decision": "READY",
    "tmqs": 100,
    "rvol": 3.0,
    "reason": "TMQS 100 strong breakout",
}

trade = engine.process_signal(signal)

print("Opened trade:")
print(trade)

print("\nPortfolio after opening:")
print(engine.summary())

latest_prices = {
    "HIVE.TO": 5.70
}

closed_trades = engine.update_positions(
    latest_prices,
    "2026-07-10"
)

print("\nClosed trades:")
print(closed_trades)

print("\nPortfolio after update:")
print(engine.summary())