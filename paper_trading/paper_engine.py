"""
Paper Trading Engine

Connects scanner signals to the paper portfolio,
position manager, trade journal, pending trade queue,
automatic next-day execution, and risk-based sizing.
"""

import threading
from datetime import datetime

from notifications.telegram_notifier import send_telegram_message
from paper_trading.journal import JOURNAL_FILE, save_trade
from paper_trading.opening_price import get_market_open_price
from paper_trading.pending_trades import PendingTradeQueue
from paper_trading.portfolio import PaperPortfolio
from paper_trading.position_manager import monitor_positions
from research.enrichment_engine import enrich_trade
from research.entry_context import (
    build_entry_context,
)
from research.market_snapshot import (
    build_market_snapshot,
    copy_market_snapshot,
)
from research.trade_path_analysis import (
    capture_trade_path,
)
from core.market_hours import TORONTO_TIMEZONE


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
    journal_file=JOURNAL_FILE,
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

        self.journal_file = journal_file

        self.risk_per_trade_percent = float(
            risk_per_trade_percent
        )

        self.max_position_percent = float(
            max_position_percent
        )

        self.max_open_positions = int(
            max_open_positions
        )

        self.last_position_size_diagnostics = {}

    def queue_signal(self, signal):
        return self.pending_trades.add_trade(signal)

    def refresh_runtime_state(self):
        """
        Reload persisted trading state before critical actions.

        This prevents a long-running GUI or headless process
        from acting on stale portfolio or pending-queue data
        written by another Northstar process.

        In-memory test doubles do not necessarily provide
        persistence reload methods, so reload only when the
        underlying object supports it.
        """
        portfolio_loader = getattr(
            self.portfolio,
            "_load_state",
            None,
        )

        if callable(portfolio_loader):
            portfolio_loader()

        pending_loader = getattr(
            self.pending_trades,
            "_load_from_csv",
            None,
        )

        if callable(pending_loader):
            pending_loader()

    def queue_eod_signals(self, scan_result):
        self.refresh_runtime_state()

        ready_signals = scan_result.get("ready", [])
        results = []

        already_open = 0
        already_pending = 0
        other_rejected = 0

        open_symbols = {
            position["symbol"]
            for position in self.portfolio.open_positions
        }

        for signal in ready_signals:
            symbol = signal["symbol"]

            if symbol in open_symbols:
                results.append(
                    {
                        "success": False,
                        "symbol": symbol,
                        "status": "ALREADY_OPEN",
                        "message": (
                            f"{symbol} already has an open position."
                        ),
                    }
                )
                already_open += 1
                continue

            result = self.queue_signal(signal)
            results.append(result)

            if not result.get("success"):
                message = result.get("message", "")

                if "already pending" in message.lower():
                    already_pending += 1
                else:
                    other_rejected += 1

        added = sum(
            1
            for result in results
            if result.get("success")
        )

        return {
            "attempted": len(ready_signals),
            "added": added,
            "rejected": (
                already_open
                + already_pending
                + other_rejected
            ),
            "already_open": already_open,
            "already_pending": already_pending,
            "other_rejected": other_rejected,
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
        self.refresh_runtime_state()

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
                price_source=price_result.get(
                    "price_source",
                    "",
                ),
                entry_market_snapshot=(
                    price_result
                ),
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
                "price_source": price_result.get(
                    "price_source",
                    "",
                ),
                "status": (
                    "EXECUTED"
                    if execution_result.get("success")
                    else "FAILED"
                ),
                "message": execution_result.get(
                    "message",
                    "Trade execution failed.",
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
        price_source="",
        entry_market_snapshot=None,
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
            diagnostics = self.last_position_size_diagnostics
            return {
                "success": False,
                "message": diagnostics.get(
                    "reason",
                    "Position sizing rejected the trade.",
                ),
                "diagnostics": diagnostics,
            }

        entry_context = build_entry_context(
            portfolio=self.portfolio,
            sizing_diagnostics=(
                self.last_position_size_diagnostics
            ),
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            shares=shares,
            atr_multiplier=atr_multiplier,
            reward_multiplier=reward_multiplier,
            max_hold_days=max_hold_days,
            signal_close=pending_trade.get(
                "signal_close",
                "",
            ),
        )

        position = {
            "symbol": symbol,
            "strategy": pending_trade.get("strategy", "MOMENTUM"),
            "signal_date": pending_trade["signal_date"],
            "signal_close": pending_trade.get(
                "signal_close",
                "",
            ),
            "signal_reason": pending_trade.get(
                "reason",
                "",
            ),
            "signal_snapshot_json": pending_trade.get(
                "signal_snapshot_json",
                "",
            ),
            "entry_date": entry_date,
            "entry_price": entry_price,
            "price_source": price_source,
            "shares": shares,
            "stop_price": stop_price,
            "target_price": target_price,
            "atr": atr,
            "tmqs": pending_trade["tmqs"],
            "rvol": pending_trade["rvol"],
            "breakout": pending_trade["breakout"],
            "max_hold_days": max_hold_days,
        }

        position.update(
            entry_context
        )

        entry_snapshot = copy_market_snapshot(
            "entry",
            entry_market_snapshot,
        )

        if not entry_snapshot:
            entry_snapshot = build_market_snapshot(
                "entry",
                entry_market_snapshot,
                source=price_source,
            )

        position.update(
            entry_snapshot
        )

        position["research"] = enrich_trade(position)

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
            diagnostics = self.last_position_size_diagnostics
            return {
                "success": False,
                "message": diagnostics.get(
                    "reason",
                    "Position sizing rejected the trade.",
                ),
                "diagnostics": diagnostics,
            }

        risk_per_share = (
            price - stop_price
        )

        derived_reward_multiple = (
            (
                target_price - price
            )
            / risk_per_share
            if risk_per_share > 0
            else 0.0
        )

        entry_context = build_entry_context(
            portfolio=self.portfolio,
            sizing_diagnostics=(
                self.last_position_size_diagnostics
            ),
            entry_price=price,
            stop_price=stop_price,
            target_price=target_price,
            shares=shares,
            atr_multiplier=signal.get(
                "atr_multiplier",
                "",
            ),
            reward_multiplier=(
                derived_reward_multiple
            ),
            max_hold_days=signal.get(
                "max_hold_days",
                10,
            ),
            signal_close=signal.get(
                "signal_close",
                signal.get(
                    "close",
                    price,
                ),
            ),
        )

        position = {
            "symbol": symbol,
            "strategy": signal.get("strategy", "MOMENTUM"),
            "signal_date": signal.get(
                "signal_date",
                signal.get(
                    "date",
                    "2026-07-09",
                ),
            ),
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

        position.update(
            entry_context
        )

        position.update(
            build_market_snapshot(
                "entry",
                signal,
                source=signal.get(
                    "data_source",
                    "",
                ),
            )
        )

        position["research"] = enrich_trade(position)
        
        result = self.portfolio.open_position(position)

        if result.get("success"):
            self._notify_trade_opened(position)

        return result

    def _send_telegram_async(self, message):
        def worker():
            try:
                result = send_telegram_message(message)

                print(f"Telegram Result: {result}")

                if not result.get("success"):
                    print(
                        "Telegram trade alert warning: "
                        f"{result.get('message', '')}"
                    )
                else:
                        print("Telegram trade alert sent successfully.")
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

        self.last_position_size_diagnostics = {
            "entry_price": entry_price,
            "stop_price": stop_price,
            "requested_shares": requested_shares,
            "decision": "REJECTED",
            "reason": "",
            "final_shares": 0,
        }

        if entry_price <= 0:
            self.last_position_size_diagnostics["reason"] = (
                "Entry price must be greater than zero."
            )
            return 0

        risk_per_share = entry_price - stop_price
        self.last_position_size_diagnostics[
            "risk_per_share"
        ] = risk_per_share

        if risk_per_share <= 0:
            self.last_position_size_diagnostics["reason"] = (
                "Stop price must be below the entry price."
            )
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

        raw_shares_by_risk = int(
            risk_budget // risk_per_share
        )

        minimum_one_share_override = (
            self.risk_model == "fixed"
            and raw_shares_by_risk == 0
        )

        if minimum_one_share_override:
            shares_by_risk = 1
        else:
            shares_by_risk = raw_shares_by_risk

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

        requested_share_limit = None

        if requested_shares is not None:
            requested_share_limit = int(requested_shares)
            allowed_shares = min(
                allowed_shares,
                requested_share_limit,
            )

        final_shares = max(allowed_shares, 0)
        actual_position_risk = (
            final_shares * risk_per_share
        )

        limits = {
            "risk": shares_by_risk,
            "allocation": shares_by_allocation,
            "cash": shares_by_cash,
        }

        if requested_share_limit is not None:
            limits["requested"] = requested_share_limit

        limiting_factor = min(
            limits,
            key=limits.get,
        )

        if final_shares <= 0:
            decision = "REJECTED"

            if shares_by_allocation <= 0:
                reason = (
                    "Entry price exceeds the maximum "
                    "position allocation."
                )
            elif shares_by_cash <= 0:
                reason = (
                    "Available cash is insufficient to "
                    "purchase one share."
                )
            elif requested_share_limit is not None and (
                requested_share_limit <= 0
            ):
                reason = (
                    "Requested share quantity must be "
                    "greater than zero."
                )
            else:
                reason = (
                    "No shares are permitted under the "
                    "current sizing limits."
                )
        elif minimum_one_share_override:
            decision = "OVERRIDE"
            reason = (
                "Minimum one-share paper research override "
                "applied because one share exceeds the "
                "configured fixed-risk budget."
            )
        else:
            decision = "ACCEPTED"
            reason = (
                "Position size accepted under the current "
                "risk, allocation, and cash limits."
            )

        self.last_position_size_diagnostics = {
            "entry_price": entry_price,
            "stop_price": stop_price,
            "risk_per_share": risk_per_share,
            "portfolio_value": portfolio_value,
            "available_cash": self.portfolio.cash,
            "risk_model": self.risk_model,
            "risk_budget": risk_budget,
            "maximum_position_value": maximum_position_value,
            "raw_shares_by_risk": raw_shares_by_risk,
            "shares_by_risk": shares_by_risk,
            "shares_by_allocation": shares_by_allocation,
            "shares_by_cash": shares_by_cash,
            "requested_shares": requested_shares,
            "final_shares": final_shares,
            "actual_position_risk": actual_position_risk,
            "minimum_one_share_override": (
                minimum_one_share_override
            ),
            "limiting_factor": limiting_factor,
            "decision": decision,
            "reason": reason,
        }

        return final_shares

    def _capture_closed_trade_path(
        self,
        trade,
    ):
        """
        Attach post-close research path metrics.

        The paper position has already been closed before this
        function runs. Research failure therefore cannot prevent
        or reverse the trading action.
        """

        try:
            path_result = (
                capture_trade_path(
                    trade
                )
            )

        except Exception as error:
            path_result = {
                "trade_path_status": "ERROR",
                "trade_path_source": "IBKR",
                "trade_path_bar_count": 0,
                "trade_path_bars_saved": 0,
                "trade_path_error": str(
                    error
                ),
            }

        trade.update(
            path_result
        )

        return path_result

    def _attach_exit_market_snapshot(
        self,
        trade,
        market_snapshot=None,
    ):
        """
        Attach best-effort exit bid/ask research.

        The paper position has already been closed before this
        function runs. Snapshot failure cannot prevent or reverse
        the trading action.
        """

        source = ""

        if isinstance(
            market_snapshot,
            dict,
        ):
            source = (
                market_snapshot.get(
                    "data_source",
                    market_snapshot.get(
                        "source",
                        "",
                    ),
                )
                or ""
            )

        try:
            snapshot = build_market_snapshot(
                "exit",
                market_snapshot,
                source=source,
                captured_at=trade.get(
                    "exit_timestamp",
                    "",
                ),
            )

        except Exception as error:
            snapshot = {
                "exit_quote_status": "ERROR",
                "exit_quote_source": source,
                "exit_quote_timestamp": (
                    trade.get(
                        "exit_timestamp",
                        "",
                    )
                ),
                "exit_bid": "",
                "exit_ask": "",
                "exit_last": "",
                "exit_midpoint": "",
                "exit_spread_amount": "",
                "exit_spread_percent": "",
                "exit_quote_error": str(
                    error
                ),
            }

        trade.update(
            snapshot
        )

        return snapshot

    def update_positions(
        self,
        latest_prices,
        current_date,
        current_datetime=None,
        market_snapshots=None,
    ):
        closed_trades = monitor_positions(
            portfolio=self.portfolio,
            current_prices=latest_prices,
            current_date=current_date,
            current_datetime=current_datetime,
        )

        for trade in closed_trades:
            market_snapshot = (
                (market_snapshots or {}).get(
                    trade["symbol"]
                )
            )

            self._attach_exit_market_snapshot(
                trade,
                market_snapshot=(
                    market_snapshot
                ),
            )

            self._capture_closed_trade_path(
                trade
            )

            save_trade(
                trade,
                file_path=self.journal_file,
            )

            self._notify_trade_closed(
                trade
            )

        return closed_trades

    def close_position(
        self,
        symbol,
        exit_price,
        current_date,
        exit_reason="Manual exit",
        current_datetime=None,
        market_snapshot=None,
    ):
        if current_datetime is None:
            current_datetime = datetime.now(
                TORONTO_TIMEZONE
            )

        elif current_datetime.tzinfo is None:
            current_datetime = (
                current_datetime.replace(
                    tzinfo=TORONTO_TIMEZONE
                )
            )

        else:
            current_datetime = (
                current_datetime.astimezone(
                    TORONTO_TIMEZONE
                )
            )

        result = self.portfolio.close_position(
            symbol=symbol,
            exit_price=exit_price,
            exit_date=current_date,
            exit_reason=exit_reason,
            exit_timestamp=(
                current_datetime.isoformat(
                    timespec="seconds"
                )
            ),
        )

        if result.get("success"):
            trade = result["trade"]

            self._attach_exit_market_snapshot(
                trade,
                market_snapshot=(
                    market_snapshot
                ),
            )

            self._capture_closed_trade_path(
                trade
            )

            save_trade(
                trade,
                file_path=self.journal_file,
            )

            self._notify_trade_closed(
                trade
            )

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
