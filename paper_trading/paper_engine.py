"""
Paper Trading Engine

Connects scanner signals to the paper portfolio,
position manager, trade journal, pending trade queue,
automatic next-day execution, and risk-based sizing.
"""

import threading

from notifications.telegram_notifier import send_telegram_message
from paper_trading.journal import save_trade
from paper_trading.opening_price import get_market_open_price
from paper_trading.pending_trades import PendingTradeQueue
from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions
from research.enrichment_engine import enrich_trade


PORTFOLIO_STATE_FILE = "paper_portfolio_state.json"
PENDING_TRADES_FILE = "pending_trades.csv"

DEFAULT_RISK_PER_TRADE_PERCENT = 1.0
DEFAULT_MAX_POSITION_PERCENT = 20.0
DEFAULT_MAX_OPEN_POSITIONS = 5


class PaperTradingEngine:
    def __init__(
    self,
    starting_cash=10000,
    portfolio_state_file=PORTFOLIO_STATE_FILE,
    pending_trades_file=PENDING_TRADES_FILE,
    risk_per_trade_percent=DEFAULT_RISK_PER_TRADE_PERCENT,
    risk_model="percent",
    fixed_risk_amount=100.0,
    max_position_percent=DEFAULT_MAX_POSITION_PERCENT,
    max_open_positions=DEFAULT_MAX_OPEN_POSITIONS,
    ):
        self.risk_model = str(risk_model).lower()
        self.fixed_risk_amount = float(fixed_risk_amount) 
        self.portfolio = PaperPortfolio(
            starting_cash=starting_cash,
            state_file=portfolio_state_file,
        )

        self.pending_trades = PendingTradeQueue(
            file_path=pending_trades_file,
        )

        self.risk_per_trade_percent = float(
            risk_per_trade_percent
        )

        self.max_position_percent = float(
            max_position_percent
        )

        self.max_open_positions = int(
            max_open_positions
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

    def execute_pending_trades_for_date(
        self,
        execution_date,
        price_provider=get_market_open_price,
        atr_multiplier=2.0,
        reward_multiplier=2.5,
        max_hold_days=10,
    ):
        pending_trades = self.pending_trades.get_all()
        results = []

        open_symbols = {
            position["symbol"]
            for position in self.portfolio.open_positions
        }

        for pending_trade in pending_trades:
            symbol = pending_trade["symbol"]
            signal_date = pending_trade["signal_date"]

            if symbol in open_symbols:
                self.pending_trades.remove_trade(symbol)

                results.append(
                    {
                        "success": False,
                        "symbol": symbol,
                        "status": "SKIPPED",
                        "message": (
                            f"{symbol} already has an open position. "
                            "Stale pending trade removed."
                        ),
                    }
                )
                continue

            if execution_date <= signal_date:
                results.append(
                    {
                        "success": False,
                        "symbol": symbol,
                        "status": "SKIPPED",
                        "message": (
                            f"{symbol} is not eligible until after "
                            f"{signal_date}."
                        ),
                    }
                )
                continue

            price_result = price_provider(
                symbol,
                execution_date,
            )

            if not price_result.get("success"):
                results.append(
                    {
                        "success": False,
                        "symbol": symbol,
                        "status": "PRICE_UNAVAILABLE",
                        "message": price_result.get(
                            "message",
                            "Opening price unavailable.",
                        ),
                    }
                )
                continue

            execution_result = self.execute_pending_trade(
                symbol=symbol,
                entry_price=price_result["open_price"],
                entry_date=execution_date,
                atr_multiplier=atr_multiplier,
                reward_multiplier=reward_multiplier,
                max_hold_days=max_hold_days,
            )

            result = {
                "success": execution_result.get(
                    "success",
                    False,
                ),
                "symbol": symbol,
                "entry_date": execution_date,
                "entry_price": price_result["open_price"],
                "status": (
                    "EXECUTED"
                    if execution_result.get("success")
                    else "FAILED"
                ),
                "message": execution_result.get(
                    "message",
                    "",
                ),
            }

            results.append(result)

        executed = sum(
            1
            for result in results
            if result["status"] == "EXECUTED"
        )

        price_unavailable = sum(
            1
            for result in results
            if result["status"] == "PRICE_UNAVAILABLE"
        )

        skipped = sum(
            1
            for result in results
            if result["status"] == "SKIPPED"
        )

        failed = sum(
            1
            for result in results
            if result["status"] == "FAILED"
        )

        return {
            "execution_date": execution_date,
            "attempted": len(pending_trades),
            "executed": executed,
            "price_unavailable": price_unavailable,
            "skipped": skipped,
            "failed": failed,
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

        if (
            len(self.portfolio.open_positions)
            >= self.max_open_positions
        ):
            return {
                "success": False,
                "message": (
                    "Maximum number of open positions "
                    f"reached ({self.max_open_positions})."
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
            entry_price=entry_price,
            stop_price=stop_price,
        )

        if shares <= 0:
            return {
                "success": False,
                "message": (
                    "Position size is zero under the current "
                    "risk and cash limits."
                ),
            }

        position = {
            "symbol": symbol,
            "strategy": pending_trade.get("strategy", "MOMENTUM"),
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
        position["research"] = enrich_trade(position)

        result = self.portfolio.open_position(position)
        result = self.portfolio.open_position(position)

        if result.get("success"):
            self.pending_trades.remove_trade(symbol)
            self._notify_trade_opened(position)

        return result

    def process_signal(self, signal):
        if signal.get("decision") != "READY":
            return None

        symbol = signal["symbol"]
        price = float(signal["price"])

        for position in self.portfolio.open_positions:
            if position["symbol"] == symbol:
                return None

        if (
            len(self.portfolio.open_positions)
            >= self.max_open_positions
        ):
            return {
                "success": False,
                "message": (
                    "Maximum number of open positions "
                    f"reached ({self.max_open_positions})."
                ),
            }

        stop_price = float(
            signal.get(
                "stop_price",
                price * 0.95,
            )
        )

        target_price = float(
            signal.get(
                "target_price",
                price * 1.125,
            )
        )

        shares = self.calculate_position_size(
            entry_price=price,
            stop_price=stop_price,
            requested_shares=signal.get("shares"),
        )

        if shares <= 0:
            return {
                "success": False,
                "message": (
                    "Position size is zero under the current "
                    "risk and cash limits."
                ),
            }

        position = {
            "symbol": symbol,
            "strategy": signal.get("strategy", "MOMENTUM"),
            "entry_date": signal.get(
                "date",
                "2026-07-09",
            ),
            "entry_price": price,
            "shares": shares,
            "stop_price": stop_price,
            "target_price": target_price,
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

        result = self.portfolio.open_position(position)

        if result.get("success"):
            self._notify_trade_opened(position)

        return result

    def _send_telegram_async(self, message):
        def worker():
            try:
                result = send_telegram_message(message)

                if not result.get("success"):
                    print(
                        "Telegram trade alert warning: "
                        f"{result.get('message', '')}"
                    )
            except Exception as error:
                print(
                    "Unexpected Telegram trade alert error: "
                    f"{error}"
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def _notify_trade_opened(self, position):
        entry_price = float(position["entry_price"])
        stop_price = float(position["stop_price"])
        target_price = float(position["target_price"])
        shares = int(position["shares"])

        risk_amount = (
            entry_price - stop_price
        ) * shares

        summary = self.portfolio.summary()

        message = (
            "PAPER TRADE OPENED\n\n"
            f"Symbol: {position['symbol']}\n"
            f"Entry: ${entry_price:.2f}\n"
            f"Shares: {shares}\n"
            f"Stop: ${stop_price:.2f}\n"
            f"Target: ${target_price:.2f}\n"
            f"Position Risk: ${risk_amount:.2f}\n\n"
            f"Available Cash: ${summary['cash']:,.2f}\n"
            f"Portfolio Value: "
            f"${summary['portfolio_value']:,.2f}\n"
            f"Open Positions: {summary['open_positions']}"
        )

        self._send_telegram_async(message)

    def calculate_position_size(
        self,
        entry_price,
        stop_price,
        requested_shares=None,
    ):
        entry_price = float(entry_price)
        stop_price = float(stop_price)

        if entry_price <= 0:
            return 0

        risk_per_share = entry_price - stop_price

        if risk_per_share <= 0:
            return 0

        portfolio_value = self.portfolio.portfolio_value()

        if self.risk_model == "fixed":
            risk_budget = self.fixed_risk_amount
        else:
            risk_budget = portfolio_value * (
                self.risk_per_trade_percent / 100
            )   
        maximum_position_value = portfolio_value * (
            self.max_position_percent / 100
        )

        shares_by_risk = int(
            risk_budget // risk_per_share
        )

        shares_by_allocation = int(
            maximum_position_value // entry_price
        )

        shares_by_cash = int(
            self.portfolio.cash // entry_price
        )

        allowed_shares = min(
            shares_by_risk,
            shares_by_allocation,
            shares_by_cash,
        )

        if requested_shares is not None:
            allowed_shares = min(
                allowed_shares,
                int(requested_shares),
            )

        return max(allowed_shares, 0)

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
            self._notify_trade_closed(trade)

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
            self._notify_trade_closed(result["trade"])

        return result

    def _notify_trade_closed(self, trade):
        profit_loss = float(
            trade.get("profit_loss", 0)
        )

        profit_loss_percent = float(
            trade.get("profit_loss_percent", 0)
        )

        exit_reason = str(
            trade.get("exit_reason", "Trade closed")
        )

        reason_title = {
            "Stop hit": "STOP HIT",
            "Target hit": "TARGET HIT",
            "Time exit": "TIME EXIT",
            "Manual exit": "MANUAL EXIT",
        }.get(
            exit_reason,
            exit_reason.upper(),
        )

        summary = self.portfolio.summary()

        message = (
            f"{reason_title}\n\n"
            f"Symbol: {trade['symbol']}\n"
            f"Entry: "
            f"${float(trade['entry_price']):.2f}\n"
            f"Exit: "
            f"${float(trade['exit_price']):.2f}\n"
            f"Shares: {int(trade['shares'])}\n"
            f"Realized P/L: "
            f"${profit_loss:+,.2f} "
            f"({profit_loss_percent:+.2f}%)\n"
            f"Exit Reason: {exit_reason}\n\n"
            f"Available Cash: "
            f"${summary['cash']:,.2f}\n"
            f"Portfolio Value: "
            f"${summary['portfolio_value']:,.2f}\n"
            f"Open Positions: "
            f"{summary['open_positions']}\n"
            f"Closed Trades: "
            f"{summary['closed_trades']}"
        )

        self._send_telegram_async(message)

    def summary(self):
        return self.portfolio.summary()
    