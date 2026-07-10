"""
Paper Trading Engine

Connects scanner signals to the paper portfolio,
position manager and trade journal.
"""

from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions
from paper_trading.journal import save_trade


class PaperTradingEngine:
    def __init__(self, starting_cash=10000):
        self.portfolio = PaperPortfolio(starting_cash=starting_cash)

    def process_signal(self, signal):
        if signal.get("decision") != "READY":
            return None

        symbol = signal["symbol"]
        price = float(signal["price"])

        # Prevent duplicate positions in the same symbol.
        for position in self.portfolio.open_positions:
            if position["symbol"] == symbol:
                return None

        shares = self.calculate_position_size(
            price,
            signal.get("shares"),
        )

        if shares <= 0:
            return None

        position = {
            "symbol": symbol,
            "entry_date": signal.get(
                "date",
                "2026-07-09",
            ),
            "entry_price": price,
            "shares": shares,
            "stop_price": signal.get(
                "stop_price",
                price * 0.95,
            ),
            "target_price": signal.get(
                "target_price",
                price * 1.125,
            ),
            "tmqs": signal.get("tmqs", 100),
            "rvol": signal.get("rvol", 2.5),
        }

        return self.portfolio.open_position(position)

    def calculate_position_size(self, price, requested_shares=None):
        if requested_shares is not None:
            return int(requested_shares)

        cash_to_use = self.portfolio.cash * 0.10
        return int(cash_to_use // price)

    def update_positions(self, latest_prices, current_date):
        closed_trades = monitor_positions(
            portfolio=self.portfolio,
            current_prices=latest_prices,
            current_date=current_date,
        )

        for trade in closed_trades:
            save_trade(trade)

        return closed_trades

    def close_position(
        self,
        symbol,
        exit_price,
        current_date,
        exit_reason="Manual exit",
    ):
        result = self.portfolio.close_position(
            symbol=symbol,
            exit_price=exit_price,
            exit_date=current_date,
            exit_reason=exit_reason,
        )

        if result.get("success"):
            save_trade(result["trade"])

        return result

    def summary(self):
        return self.portfolio.summary()