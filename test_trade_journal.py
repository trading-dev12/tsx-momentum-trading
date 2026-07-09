from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions
from paper_trading.journal import save_trade


portfolio = PaperPortfolio(starting_cash=10000)

position = {
    "symbol": "SHOP.TO",
    "entry_date": "2026-07-09",
    "entry_price": 100.00,
    "shares": 10,
    "stop_price": 95.00,
    "target_price": 112.50,
    "tmqs": 100,
    "rvol": 2.5,
}

portfolio.open_position(position)

current_prices = {
    "SHOP.TO": 113.00,
}

closed_trades = monitor_positions(
    portfolio=portfolio,
    current_prices=current_prices,
    current_date="2026-07-10",
)

for trade in closed_trades:
    save_trade(trade)

print("Closed trades saved to paper_trade_journal.csv")
print(portfolio.summary())