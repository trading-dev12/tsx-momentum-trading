from paper_trading.paper_engine import PaperTradingEngine
from paper_trading.dashboard import display_paper_dashboard


engine = PaperTradingEngine(starting_cash=10000)

signal = {
    "symbol": "HIVE.TO",
    "price": 5.00,
    "decision": "READY",
    "tmqs": 100,
    "rvol": 3.0,
    "reason": "TMQS 100 strong breakout",
}

engine.process_signal(signal)

current_prices = {
    "HIVE.TO": 5.35
}

display_paper_dashboard(engine, current_prices)

closed_trades = engine.update_positions(
    {"HIVE.TO": 5.70},
    "2026-07-10"
)

print("\nAFTER POSITION UPDATE\n")

display_paper_dashboard(engine, {"HIVE.TO": 5.70})