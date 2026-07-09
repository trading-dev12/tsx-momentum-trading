from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions


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

print("Before monitoring:")
print(portfolio.summary())

current_prices = {
    "SHOP.TO": 113.00,
}

closed_trades = monitor_positions(
    portfolio=portfolio,
    current_prices=current_prices,
    current_date="2026-07-10",
)

print("\nClosed trades:")
print(closed_trades)

print("\nAfter monitoring:")
print(portfolio.summary())