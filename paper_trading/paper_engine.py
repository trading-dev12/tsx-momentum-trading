"""
Paper Trading Engine

Connects scanner signals to the paper portfolio,
position manager, trade journal, and pending trade queue.
"""

from paper_trading.journal import save_trade
from paper_trading.pending_trades import PendingTradeQueue
from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions


PORTFOLIO_STATE_FILE = "paper_portfolio_state.json"
PENDING_TRADES_FILE = "pending_trades.csv"


class PaperTradingEngine:
    def __init__(
        self,
        starting_cash=10000,
        portfolio_state_file=PORTFOLIO_STATE_FILE,
        pending_trades_file=PENDING_TRADES_FILE,
    ):
        self.portfolio = PaperPortfolio(
            starting_cash=starting_cash,
            state_file=portfolio_state_file,
        )

        self.pending_trades = PendingTradeQueue(
            file_path=pending_trades_file,
        )

    def queue_signal(self, signal):
        return self.pending_trades.add_trade(signal)

    def queue_eod_signals(self, scan_result):
        ready_signals = scan_result.get("ready", [])
        results = []

        for signal in ready_signals:
            result = self.queue_signal(signal)
            results.append(result)

        added = sum(
            1
            for result in results
            if result.get("success")
        )

        rejected = len(results) - added

        return {
            "attempted": len(ready_signals),
            "added": added,
            "rejected": rejected,
            "results": results,
        }

    def execute_pending_trade(
        self,
        symbol,
        entry_price,
        entry_date,
        atr_multiplier=2.0,
        reward_multiplier=2.5,
        max_hold_days=10,
    ):
        pending_trade = self.pending_trades.get_trade(symbol)

        if pending_trade is None:
            return {
                "success": False,
                "message": f"{symbol} is not pending.",
            }

        for position in self.portfolio.open_positions:
            if position["symbol"] == symbol:
                return {
                    "success": False,
                    "message": (
                        f"{symbol} already has "
                        "an open position."
                    ),
                }

        if entry_date <= pending_trade["signal_date"]:
            return {
                "success": False,
                "message": (
                    "Pending trades must be executed after "
                    "the signal date."
                ),
            }

        entry_price = float(entry_price)
        atr = float(pending_trade["atr"])

        stop_price = entry_price - (
            atr * atr_multiplier
        )

        risk_per_share = entry_price - stop_price

        target_price = entry_price + (
            risk_per_share * reward_multiplier
        )

        shares = self.calculate_position_size(
            entry_price,
        )

        if shares <= 0:
            return {
                "success": False,
                "message": "Position size is zero.",
            }

        position = {
            "symbol": symbol,
            "signal_date": pending_trade["signal_date"],
            "entry_date": entry_date,
            "entry_price": entry_price,
            "shares": shares,
            "stop_price": stop_price,
            "target_price": target_price,
            "atr": atr,
            "tmqs": pending_trade["tmqs"],
            "rvol": pending_trade["rvol"],
            "breakout": pending_trade["breakout"],
            "max_hold_days": max_hold_days,
        }

        result = self.portfolio.open_position(position)

        if result.get("success"):
            self.pending_trades.remove_trade(symbol)

        return result

    def process_signal(self, signal):
        if signal.get("decision") != "READY":
            return None

        symbol = signal["symbol"]
        price = float(signal["price"])

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
            "tmqs": signal.get(
                "tmqs",
                100,
            ),
            "rvol": signal.get(
                "rvol",
                2.5,
            ),
            "max_hold_days": signal.get(
                "max_hold_days",
                10,
            ),
        }

        return self.portfolio.open_position(position)

    def calculate_position_size(
        self,
        price,
        requested_shares=None,
    ):
        if requested_shares is not None:
            return int(requested_shares)

        cash_to_use = self.portfolio.cash * 0.10

        return int(cash_to_use // price)

    def update_positions(
        self,
        latest_prices,
        current_date,
    ):
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