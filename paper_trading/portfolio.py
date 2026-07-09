"""
Paper Trading Portfolio

Tracks virtual cash, open positions, and closed trades.
"""


class PaperPortfolio:
    def __init__(self, starting_cash=10000):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.open_positions = []
        self.closed_trades = []

    def can_open_position(self, position_cost):
        return self.cash >= position_cost

    def open_position(self, position):
        position_cost = position["shares"] * position["entry_price"]

        if not self.can_open_position(position_cost):
            return {
                "success": False,
                "message": "Not enough virtual cash to open position.",
            }

        self.cash -= position_cost
        self.open_positions.append(position)

        return {
            "success": True,
            "message": "Paper position opened.",
        }

    def close_position(self, symbol, exit_price, exit_date, exit_reason):
        for position in self.open_positions:
            if position["symbol"] == symbol:
                proceeds = position["shares"] * exit_price
                self.cash += proceeds

                profit_loss = proceeds - (
                    position["shares"] * position["entry_price"]
                )

                profit_loss_percent = (
                    profit_loss / (position["shares"] * position["entry_price"])
                ) * 100

                closed_trade = position.copy()
                closed_trade["exit_price"] = exit_price
                closed_trade["exit_date"] = exit_date
                closed_trade["exit_reason"] = exit_reason
                closed_trade["profit_loss"] = profit_loss
                closed_trade["profit_loss_percent"] = profit_loss_percent

                self.closed_trades.append(closed_trade)
                self.open_positions.remove(position)

                return {
                    "success": True,
                    "message": "Paper position closed.",
                    "trade": closed_trade,
                }

        return {
            "success": False,
            "message": "Open position not found.",
        }

    def portfolio_value(self, current_prices=None):
        value = self.cash

        if current_prices is None:
            current_prices = {}

        for position in self.open_positions:
            symbol = position["symbol"]
            current_price = current_prices.get(symbol, position["entry_price"])
            value += position["shares"] * current_price

        return value

    def summary(self, current_prices=None):
        value = self.portfolio_value(current_prices)

        total_return = (
            ((value - self.starting_cash) / self.starting_cash) * 100
            if self.starting_cash > 0
            else 0
        )

        return {
            "starting_cash": self.starting_cash,
            "cash": self.cash,
            "portfolio_value": value,
            "total_return": total_return,
            "open_positions": len(self.open_positions),
            "closed_trades": len(self.closed_trades),
        }