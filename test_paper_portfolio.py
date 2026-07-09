from paper_trading.portfolio import PaperPortfolio


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

print(portfolio.summary())

result = portfolio.open_position(position)
print(result)
print(portfolio.summary())

result = portfolio.close_position(
    symbol="SHOP.TO",
    exit_price=110.00,
    exit_date="2026-07-10",
    exit_reason="Target hit",
)

print(result)
print(portfolio.summary())