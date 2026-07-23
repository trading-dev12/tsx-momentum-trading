import json
import socket
import subprocess
import sys
from pathlib import Path
import logging

from shlex import quote
import tkinter as tk
from core.market_hours import get_tsx_market_status
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import threading
from core.eod_signal_service import scan_eod_signals

from paper_trading.dashboard import build_paper_dashboard_text
from notifications.telegram_notifier import send_telegram_message
from core.config_loader import load_settings
from core.watchlist_loader import load_all_watchlists
from core.market_data import get_quotes
from core.market_context import score_market_context
from paper_trading.paper_engine import PaperTradingEngine
from paper_trading.automatic_execution import (
    start_automatic_execution_service,
)
from paper_trading.automatic_eod import (
    start_automatic_eod_service,
)
from gui.system_health_panel import (
    SystemHealthPanel,
)
LOG_FOLDER = Path(__file__).resolve().parent.parent / "logs"
LOG_FOLDER.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_FOLDER / "workstation.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

class TradingWorkstation:
    def __init__(self, root):
        self.notified_ready_symbols = set()
        self.root = root
        self.root.title("TSX Momentum Pro")
        self.root.geometry("1450x760")
        self.current_view = "LIVE"

        self.mobile_dashboard_process = None
        self.mobile_dashboard_started_here = False

        self.start_mobile_dashboard()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_interval_seconds = 30
        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.latest_quotes = []
        self.previous_ready_symbols = None
        self.last_successful_refresh = None
        self.paper_engine = PaperTradingEngine(
            starting_cash=500000,
            risk_model="fixed",
            fixed_risk_amount=100.0,
            max_open_positions=100,
        )
        self.automatic_execution_thread = (
            start_automatic_execution_service(
                self.paper_engine,
            )
        )
        self.automatic_eod_thread = (
            start_automatic_eod_service(
                self.paper_engine,
                live_snapshot_provider=lambda: list(
                    self.latest_quotes
                ),
            )
        )

        self.market_label = tk.Label(
            root,
            text="Market Health: Loading...",
            font=("Arial", 16, "bold"),
            anchor="w",
        )
        self.market_label.pack(fill="x", padx=10, pady=5)

        self.summary_label = tk.Label(
            root,
            text="Scanner Summary: Loading...",
            font=("Arial", 12),
            anchor="w",
        )
        self.summary_label.pack(fill="x", padx=10, pady=5)

        self.best_trade_label = tk.Label(
            root,
            text="Best Trade Candidate: Loading...",
            font=("Arial", 13, "bold"),
            anchor="w",
            bg="#e8f0fe",
            padx=8,
            pady=6,
        )
        self.best_trade_label.pack(fill="x", padx=10, pady=5)

        button_frame = tk.Frame(root)
        button_frame.pack(fill="x", padx=10, pady=5)

        self.refresh_button = tk.Button(
            button_frame,
            text="Refresh Scanner",
            command=self.refresh_data,
            font=("Arial", 11, "bold"),
        )
        self.refresh_button.pack(side="left")

        self.eod_button = tk.Button(
            button_frame,
            text="End-of-Day Signals",
            command=self.load_eod_data,
            font=("Arial", 11, "bold"),
        )

        self.eod_button.pack(side="left", padx=(10, 0))

        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = (
            "rank",
            "symbol",
            "price",
            "tmqs",
            "confidence",
            "rvol",
            "rvol_grade",
            "breakout",
            "momentum",
            "liquidity",
            "decision",
            "reason",
        )

        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=22)

        headings = {
            "rank": "#",
            "symbol": "Symbol",
            "price": "Price",
            "tmqs": "TMQS",
            "confidence": "Confidence",
            "rvol": "RVOL",
            "rvol_grade": "RVOL Grade",
            "breakout": "Breakout",
            "momentum": "Momentum",
            "liquidity": "Liquidity",
            "decision": "Decision",
            "reason": "Reason",
        }

        for column, title in headings.items():
            self.tree.heading(column, text=title)

        self.tree.column("rank", width=45, anchor="center")
        self.tree.column("symbol", width=85, anchor="center")
        self.tree.column("price", width=90, anchor="center")
        self.tree.column("tmqs", width=70, anchor="center")
        self.tree.column("confidence", width=90, anchor="center")
        self.tree.column("rvol", width=75, anchor="center")
        self.tree.column("rvol_grade", width=90, anchor="center")
        self.tree.column("breakout", width=145, anchor="center")
        self.tree.column("momentum", width=90, anchor="center")
        self.tree.column("liquidity", width=90, anchor="center")
        self.tree.column("decision", width=100, anchor="center")
        self.tree.column("reason", width=180, anchor="w")

        self.tree.tag_configure("READY", background="#b6d7a8")
        self.tree.tag_configure("WATCH", background="#fff2cc")
        self.tree.tag_configure("IGNORE", background="#f4cccc")

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_trade_checklist)

        checklist_frame = tk.Frame(main_frame, width=420)
        checklist_frame.pack(side="right", fill="y", padx=(10, 0))

        checklist_title = tk.Label(
            checklist_frame,
            text="Trade Checklist",
            font=("Arial", 14, "bold"),
            anchor="w",
        )
        checklist_title.pack(fill="x", pady=(0, 5))

        self.checklist_text = tk.Text(
            checklist_frame,
            width=48,
            height=16,
            font=("Consolas", 13),
            wrap="word",
        )
        self.checklist_text.pack(fill="x")
        self.checklist_text.insert("1.0", "Click a stock to view details.")
        self.checklist_text.config(state="disabled")

        self.open_paper_trade_button = tk.Button(
            checklist_frame,
            text="Open Paper Trade",
            command=self.open_selected_paper_trade,
            font=("Arial", 11, "bold"),
        )
        self.open_paper_trade_button.pack(fill="x", pady=(10, 5))

        self.close_paper_trade_button = tk.Button(
            checklist_frame,
            text="Close Selected Paper Trade",
            command=self.close_selected_paper_trade,
            font=("Arial", 11, "bold"),
        )
        self.close_paper_trade_button.pack(fill="x", pady=(0, 10))
        self.market_session_label = tk.Label(
            root,
            text="TSX Session: Checking...",
            font=("Arial", 11, "bold"),
            anchor="w",
        )
        self.market_session_label.pack(fill="x", padx=10, pady=(0, 5))
        self.system_health_panel = SystemHealthPanel(root)

        self.system_health_panel.pack(
            fill="x",
            padx=10,
            pady=(0,5),
        )
        portfolio_title = tk.Label(
            checklist_frame,
            text="════════  TRADER CONTROL CENTER  ════════",
            font=("Arial", 14, "bold"),
            anchor="w",
        )
        portfolio_title.pack(fill="x", pady=(8, 5))

        self.paper_portfolio_text = tk.Text(
            checklist_frame,
            width=48,
            height=22,
            font=("Consolas", 13),
            wrap="word",
        )
        self.paper_portfolio_text.pack(fill="both", expand=True)
        self.paper_portfolio_text.config(state="disabled")
        self.paper_portfolio_text.tag_configure(
            "heading",
            foreground="#4FC3F7",
            font=("Consolas", 10, "bold"),
        )

        self.paper_portfolio_text.tag_configure(
            "profit",
            foreground="#4CAF50",
            font=("Consolas", 10, "bold"),
        )

        self.paper_portfolio_text.tag_configure(
            "loss",
            foreground="#F44336",
            font=("Consolas", 10, "bold"),
        )

        self.paper_portfolio_text.tag_configure(
            "warning",
            foreground="#FFB300",
            font=("Consolas", 10, "bold"),
        )
        self.status_label = tk.Label(
            root,
            text="Starting...",
            font=("Arial", 10),
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=10, pady=5)

        self.refresh_data()
        self.update_countdown()

    def refresh_data(self):
        self.current_view = "LIVE"
        if self.is_refreshing:
                return

        self.is_refreshing = True
        logging.info("Refresh started")
        self.refresh_button.config(state="disabled", text="Refreshing...")
        self.status_label.config(text="Refreshing data...")

        thread = threading.Thread(target=self.load_data)
        thread.daemon = True
        thread.start()
    def load_eod_data(self):
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.eod_button.config(
            state="disabled",
            text="Loading EOD Signals...",
        )
        self.status_label.config(
            text="Scanning completed daily candles...",
        )

        def worker():
            try:
                results = scan_eod_signals()

                def finish_scan():
                    ready_count = len(results["ready"])
                    watch_count = len(results["watch"])
                    ignore_count = len(results["ignore"])
                    error_count = len(results["errors"])

                    self.status_label.config(
                        text=(
                            f"EOD scan complete | "
                            f"READY: {ready_count} | "
                            f"WATCH: {watch_count} | "
                            f"IGNORE: {ignore_count} | "
                            f"ERRORS: {error_count}"
                        )
                    )

                    self.eod_button.config(
                        state="normal",
                        text="End-of-Day Signals",
                    )
                    self.is_refreshing = False

                    self.display_eod_results(results)
                    print("Displaying EOD results...")
                    print("Finished displaying EOD results.")

                self.root.after(0, finish_scan)

            except Exception as error:
                def show_eod_error():
                    self.eod_button.config(
                        state="normal",
                        text="End-of-Day Signals",
                    )
                    self.is_refreshing = False
                    self.show_error(error)

                self.root.after(0, show_eod_error)

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def load_data(self):
        try:
            settings = load_settings()
            print(f"[{datetime.now()}] load_data() started")
            watchlist = load_all_watchlists()
            market = score_market_context()
            quotes = get_quotes(watchlist)
            
            print(f"[{datetime.now()}] Quotes downloaded: {len(quotes)}")

            self.root.after(
                0,
                lambda: self.update_dashboard(market, quotes),
            )

        except Exception as error:
            self.root.after(
                0,
                lambda error=error: self.show_error(error),
            )
    def display_eod_results(self, results):
        self.current_view = "EOD"
        
        eod_quotes = results["ready"] + results["watch"]
        queue_summary = self.paper_engine.queue_eod_signals(results)

        print(
            (
            "Queued "
            f"{queue_summary['added']} READY signals "
            f"({queue_summary['rejected']} duplicates)."
            )
        )
        self.latest_quotes = eod_quotes

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.summary_label.config(
            text=(
                f"EOD Signals | "
                f"READY: {len(results['ready'])} | "
                f"Queued: {queue_summary['added']} | "
                f"Duplicates: {queue_summary['rejected']} | "
                f"WATCH: {len(results['watch'])} | "
                f"IGNORE: {len(results['ignore'])} | "
                f"ERRORS: {len(results['errors'])}"
            )
        )

        if eod_quotes:
            best = max(
                eod_quotes,
                key=lambda quote: (
                    quote["tmqs"],
                    quote["rvol"],
                ),
            )

            self.best_trade_label.config(
                text=(
                    f"Best EOD Candidate: {best['symbol']} | "
                    f"Decision: {best['decision']} | "
                    f"TMQS: {best['tmqs']} | "
                    f"RVOL: {best['rvol']:.2f}x | "
                    f"Breakout: {best['breakout']} | "
                    f"Signal Date: {best['signal_date']} | "
                    f"Next Trading Day Entry"
                ),
                bg=(
                    "#b6d7a8"
                    if best["decision"] == "READY"
                    else "#fff2cc"
                ),
            )
        else:
            self.best_trade_label.config(
                text="Best EOD Candidate: None",
                bg="#e8f0fe",
            )

        for rank, quote in enumerate(eod_quotes, start=1):
            self.tree.insert(
                "",
                "end",
                iid=str(rank - 1),
                values=(
                    rank,
                    quote["symbol"],
                    f"{quote['close']:.2f}",
                    quote["tmqs"],
                    "--",
                    f"{quote['rvol']:.2f}x",
                    "--",
                    quote["breakout"],
                    "--",
                    "--",
                    quote["decision"],
                    quote["reason"],
                ),
                tags=(quote["decision"],),
            )
    def update_dashboard(self, market, quotes):
        self.latest_quotes = quotes
        self.last_successful_refresh = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.check_ready_alerts(quotes)
        self.monitor_paper_positions()

        for row in self.tree.get_children():
            self.tree.delete(row)

        tsx = self.format_percent(market["tsx_change"])
        oil = self.format_percent(market["oil_change"])
        bitcoin = self.format_percent(market["bitcoin_change"])
        vix = self.format_percent(market["vix_change"])

        self.market_label.config(
            text=(
                f"Market Health: {market['status']} | "
                f"Score: {market['score']}/100 | "
                f"TSX: {tsx} | Oil: {oil} | "
                f"Bitcoin: {bitcoin} | VIX: {vix}"
            )
        )

        total = len(quotes)
        ready = sum(1 for q in quotes if q["decision"] == "READY")
        watch = sum(1 for q in quotes if q["decision"] == "WATCH")
        ignore = sum(1 for q in quotes if q["decision"] == "IGNORE")
        average_tmqs = sum(q["tmqs"] for q in quotes) / total if total else 0

        ready_quotes = [q for q in quotes if q["decision"] == "READY"]
        watch_quotes = [q for q in quotes if q["decision"] == "WATCH"]

        if ready_quotes:
            best = max(ready_quotes, key=lambda q: q["tmqs"])
        elif watch_quotes:
            best = max(watch_quotes, key=lambda q: q["tmqs"])
        else:
            best = max(quotes, key=lambda q: q["tmqs"]) if total else None

        best_text = best["symbol"] if best else "N/A"

        self.summary_label.config(
            text=(
                f"Stocks Scanned: {total} | "
                f"READY: {ready} | WATCH: {watch} | IGNORE: {ignore} | "
                f"Average TMQS: {average_tmqs:.1f} | "
                f"Best Candidate: {best_text}"
            )
        )

        self.update_best_trade_banner(best)

        for rank, quote in enumerate(quotes, start=1):
            decision = quote["decision"]
            reason = quote.get("reason", "")
            rvol_grade = quote.get("grades", {}).get("RVOL", "N/A")
            confidence = quote.get("confidence_score", 0)

            self.tree.insert(
                "",
                "end",
                iid=str(rank - 1),
                values=(
                    rank,
                    quote["symbol"],
                    f"{quote['price']:.2f}",
                    quote["tmqs"],
                    f"{confidence}%",
                    f"{quote['relative_volume']:.2f}x",
                    rvol_grade,
                    quote["breakout_status"],
                    quote["grades"]["Momentum"],
                    quote["grades"]["Liquidity"],
                    decision,
                    reason,
                ),
                tags=(decision,),
            )
        self.update_paper_portfolio_panel()

        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.refresh_button.config(state="normal", text="Refresh Scanner")

    def update_best_trade_banner(self, best):
        if not best:
            self.best_trade_label.config(
                text="Best Trade Candidate: N/A",
                bg="#e8f0fe",
            )
            return

        decision = best["decision"]

        if decision == "READY":
            banner_color = "#b6d7a8"
        elif decision == "WATCH":
            banner_color = "#fff2cc"
        else:
            banner_color = "#f4cccc"

        self.best_trade_label.config(
            text=(
                f"Best Trade Candidate: {best['symbol']} | "
                f"Decision: {decision} | "
                f"TMQS: {best['tmqs']} | "
                f"Confidence: {best.get('confidence_score', 0)}% | "
                f"RVOL: {best['relative_volume']:.2f}x | "
                f"Breakout: {best['breakout_status']} | "
                f"Reason: {best.get('reason', '')}"
            ),
            bg=banner_color,
        )

    def check_ready_alerts(self, quotes):
        current_ready_symbols = {
            q["symbol"] for q in quotes if q["decision"] == "READY"
        }

        if self.previous_ready_symbols is None:
            self.previous_ready_symbols = current_ready_symbols
            self.notified_ready_symbols.update(current_ready_symbols)
            return

        new_ready_symbols = (
            current_ready_symbols
            - self.notified_ready_symbols
        )

        if new_ready_symbols:
            print(
                "NEW READY ALERT:",
                ", ".join(sorted(new_ready_symbols)),
            )

            ready_quotes = [
                quote
                for quote in quotes
                if quote["symbol"] in new_ready_symbols
            ]

            message_lines = [
                "TSX MOMENTUM PRO - NEW READY ALERT",
                "",
            ]

            for ready_quote in ready_quotes:
                message_lines.extend(
                    [
                        f"Symbol: {ready_quote['symbol']}",
                        (
                            "Price: "
                            f"${float(ready_quote.get('price', 0)):.2f}"
                        ),
                        (
                            "TMQS: "
                            f"{ready_quote.get('tmqs', 0)}"
                        ),
                        (
                            "Confidence: "
                            f"{ready_quote.get('confidence_score', 0)}%"
                        ),
                        (
                            "RVOL: "
                            f"{float(ready_quote.get('relative_volume', 0)):.2f}x"
                        ),
                        (
                            "Breakout: "
                            f"{ready_quote.get('breakout_status', '')}"
                        ),
                        (
                            "Reason: "
                            f"{ready_quote.get('reason', '')}"
                        ),
                        "",
                    ]
                )

            telegram_message = "\n".join(message_lines).strip()

            def send_ready_telegram_alert():
                try:
                    result = send_telegram_message(
                        telegram_message
                    )

                    if not result.get("success"):
                        print(
                            "Telegram READY alert warning: "
                            f"{result.get('message', '')}"
                        )
                except Exception as error:
                    print(
                        "Unexpected Telegram READY alert error: "
                        f"{error}"
                    )

            threading.Thread(
                target=send_ready_telegram_alert,
                daemon=True,
            ).start()

        self.notified_ready_symbols.update(new_ready_symbols)

    def show_trade_checklist(self, event):
        selected = self.tree.selection()

        if not selected:
            return

        index = int(selected[0])

        if index >= len(self.latest_quotes):
            return

        quote = self.latest_quotes[index]
        checklist = self.build_checklist_text(quote)

        self.checklist_text.config(state="normal")
        self.checklist_text.delete("1.0", tk.END)
        self.checklist_text.insert("1.0", checklist)
        self.checklist_text.config(state="disabled")

    def build_checklist_text(self, quote):
        symbol = quote["symbol"]
        price = quote["price"]
        tmqs = quote["tmqs"]
        confidence = quote.get("confidence_score", 0)
        rvol = quote["relative_volume"]
        rvol_grade = quote.get("grades", {}).get("RVOL", "N/A")
        breakout = quote["breakout_status"]
        momentum = quote["grades"]["Momentum"]
        liquidity = quote["grades"]["Liquidity"]
        decision = quote["decision"]
        reason = quote.get("reason", "")
        atr = quote.get("atr", 0)
        stop_price = price - (atr * 2.0) if atr > 0 else 0
        risk_per_share = price - stop_price if stop_price > 0 else 0
        target_price = (
        price + (risk_per_share * 2.5)
        if risk_per_share > 0
        else 0
    )

        rvol_check = "PASS" if rvol >= 0.75 else "FAIL"
        breakout_check = "PASS" if breakout in ["BREAKOUT", "NEAR BREAKOUT"] else "FAIL"
        momentum_check = "PASS" if momentum in ["A", "B"] else "FAIL"
        liquidity_check = "PASS" if liquidity in ["A", "B"] else "FAIL"

        return (
            f"{symbol}\n"
            f"{'-' * 32}\n"
            f"Price:        ${price:.2f}\n"
            f"ATR:          ${atr:.2f}\n"
            f"Stop:         ${stop_price:.2f}\n"
            f"Target:       ${target_price:.2f}\n"
            f"TMQS:         {tmqs}\n"
            f"Confidence:   {confidence}%\n"
            f"Decision:     {decision}\n"
            f"Reason:       {reason}\n\n"
            f"Checklist\n"
            f"{'-' * 32}\n"
            f"RVOL:         {rvol:.2f}x ({rvol_grade}) [{rvol_check}]\n"
            f"Breakout:     {breakout} [{breakout_check}]\n"
            f"Momentum:     {momentum} [{momentum_check}]\n"
            f"Liquidity:    {liquidity} [{liquidity_check}]\n\n"
            f"Rule Notes\n"
            f"{'-' * 32}\n"
            f"READY needs strong TMQS, strong RVOL,\n"
            f"good breakout, momentum, and liquidity.\n\n"
            f"WATCH needs TMQS >= 60, RVOL >= 0.75,\n"
            f"and acceptable momentum/liquidity.\n"
        )

    def show_error(self, error):
        self.is_refreshing = False
        self.status_label.config(text=f"Error: {error}")
        self.refresh_button.config(state="normal", text="Refresh Scanner")

    def open_selected_paper_trade(self):
        if self.current_view == "EOD":
            messagebox.showinfo(
                "Next Trading Day Entry Required",
                (
                    "End-of-day signals are based on the completed daily candle.\n\n"
                    "Paper trades must be opened on the next trading day using "
                    "the executable entry price, not the signal-day closing price."
                ),
            )
            return
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "No Stock Selected",
                "Please select a stock first.",
            )
            return

        index = int(selected[0])

        if index >= len(self.latest_quotes):
            messagebox.showerror(
                "Error",
                "Selected stock could not be found.",
            )
            return

        quote = self.latest_quotes[index]

        if quote["decision"] != "READY":
            messagebox.showinfo(
                "Not Ready",
                f"{quote['symbol']} is not a READY trade.",
            )
            return

        symbol = quote["symbol"]
        price = float(quote["price"])
        atr = float(quote.get("atr", 0))

        if atr <= 0:
            messagebox.showwarning(
                "ATR Unavailable",
                (
                    f"ATR data is unavailable for {symbol}.\n\n"
                    "The paper trade cannot be opened safely."
                ),
            )
            return
    

        investment_amount = simpledialog.askfloat(
            "Paper Trade Position Size",
            (
                f"How much would you like to invest in {symbol}?\n\n"
                f"Current Price: ${price:.2f}\n"
                f"Available Cash: ${self.paper_engine.portfolio.cash:,.2f}"
            ),
            minvalue=price,
            maxvalue=self.paper_engine.portfolio.cash,
        )

        if investment_amount is None:
            return

        shares = int(investment_amount // price)

        if shares <= 0:
            messagebox.showwarning(
                "Invalid Position Size",
                "The investment amount is too small to purchase one share.",
            )
            return

        actual_cost = shares * price

        atr_multiplier = 2.0
        reward_multiplier = 2.5

        stop_price = price - (atr * atr_multiplier)
        risk_per_share = price - stop_price
        target_price = price + (risk_per_share * reward_multiplier)
        signal = {
            "symbol": symbol,
            "price": price,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "decision": quote["decision"],
            "tmqs": quote["tmqs"],
            "rvol": quote["relative_volume"],
            "reason": quote.get("reason", ""),
            "shares": shares,
            "atr": atr,
            "stop_price": stop_price,
            "target_price": target_price,
        }

        confirm = messagebox.askyesno(
            "Open Paper Trade",
            (
                f"Open paper trade for {symbol}?\n\n"
                f"Entry Price: ${price:.2f}\n"
                f"Shares: {shares}\n"
                f"Position Cost: ${actual_cost:,.2f}\n\n"
                f"ATR: ${atr:.2f}\n"
                f"Stop Price: ${stop_price:.2f}\n"
                f"Target Price: ${target_price:.2f}\n"
                f"Risk Per Share: ${risk_per_share:.2f}\n"
                f"Total Position Risk: ${(shares * risk_per_share):,.2f}\n\n"
                f"TMQS: {signal['tmqs']}\n"
                f"RVOL: {signal['rvol']:.2f}x"
            ),
        )

        if not confirm:
            return

        result = self.paper_engine.process_signal(signal)

        if result is None:
            messagebox.showinfo(
                "No Trade Opened",
                "No paper trade was opened.",
            )
        elif result["success"]:
            messagebox.showinfo(
                "Paper Trade Opened",
                result["message"],
            )
        else:
            messagebox.showwarning(
                "Trade Failed",
                result["message"],
            )

        self.update_paper_portfolio_panel()
    def close_selected_paper_trade(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "No Stock Selected",
                "Please select a stock first."
            )
            return

        index = int(selected[0])

        if index >= len(self.latest_quotes):
            messagebox.showerror(
                "Error",
                "Selected stock could not be found."
            )
            return

        quote = self.latest_quotes[index]
        symbol = quote["symbol"]

        current_price = quote["price"]

        confirm = messagebox.askyesno(
            "Close Paper Trade",
            f"Close paper trade for {symbol} at ${current_price:.2f}?"
        )

        if not confirm:
            return

        result = self.paper_engine.close_position(
            symbol=symbol,
            exit_price=current_price,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

        if result.get("success"):
            messagebox.showinfo(
                "Trade Closed",
                result["message"]
            )
        else:
            messagebox.showwarning(
                "Unable to Close",
                result["message"]
            )

        self.update_paper_portfolio_panel()
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "No Stock Selected",
                "Select the stock position you want to close.",
            )
            return

        index = int(selected[0])

        if index >= len(self.latest_quotes):
            messagebox.showerror(
                "Error",
                "The selected stock could not be found.",
            )
            return

        quote = self.latest_quotes[index]
        symbol = quote["symbol"]
        current_price = float(quote["price"])

        open_symbols = {
            position["symbol"]
            for position in self.paper_engine.portfolio.open_positions
        }

        if symbol not in open_symbols:
            messagebox.showinfo(
                "No Open Position",
                f"There is no open paper position for {symbol}.",
            )
            return

        confirm = messagebox.askyesno(
            "Close Paper Trade",
            (
                f"Close the open paper position for {symbol}?\n\n"
                f"Current Price: ${current_price:.2f}"
            ),
        )

        if not confirm:
            return

        current_date = datetime.now().strftime("%Y-%m-%d")

        result = self.paper_engine.close_position(
            symbol=symbol,
            exit_price=current_price,
            current_date=current_date,
            exit_reason="Manual exit",
        )

        if result.get("success"):
            trade = result["trade"]

            messagebox.showinfo(
                "Paper Trade Closed",
                (
                    f"{symbol} was closed successfully.\n\n"
                    f"Exit Price: ${trade['exit_price']:.2f}\n"
                    f"Profit/Loss: ${trade['profit_loss']:.2f}\n"
                    f"Return: {trade['profit_loss_percent']:.2f}%"
                ),
            )
        else:
            messagebox.showwarning(
                "Close Failed",
                result.get("message", "The position could not be closed."),
            )

        self.update_paper_portfolio_panel()

    def monitor_paper_positions(self):
        if not self.paper_engine.portfolio.open_positions:
            return

        current_prices = {
            quote["symbol"]: quote["price"]
            for quote in self.latest_quotes
        }

        current_date = datetime.now().strftime("%Y-%m-%d")

        closed_trades = self.paper_engine.update_positions(
            latest_prices=current_prices,
            current_date=current_date,
        )

        for trade in closed_trades:
            telegram_message = (
                "Northstar Quant - Paper Trade Closed\n\n"
                f"Symbol: {trade['symbol']}\n"
                f"Exit Price: ${trade['exit_price']:.2f}\n"
                f"Reason: {trade['exit_reason']}\n"
                f"Profit/Loss: ${trade['profit_loss']:.2f}\n"
                f"Return: {trade['profit_loss_percent']:.2f}%"
            )

            def send_closed_trade_telegram_alert(
                message=telegram_message,
            ):
                try:
                    result = send_telegram_message(message)

                    if not result.get("success"):
                        print(
                            "Telegram closed-trade alert warning: "
                            f"{result.get('message', '')}"
                        )
                except Exception as error:
                    print(
                        "Unexpected Telegram closed-trade alert error: "
                        f"{error}"
                    )

            threading.Thread(
                target=send_closed_trade_telegram_alert,
                daemon=True,
            ).start()
    def update_paper_portfolio_panel(self):
        current_prices = {}

        for quote_data in self.latest_quotes:
            current_prices[quote_data["symbol"]] = quote_data["price"]

        runtime_folder = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "runtime"
        )

        runtime_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        latest_prices_file = (
            runtime_folder / "latest_prices.json"
        )

        temporary_file = (
            runtime_folder / "latest_prices.tmp"
        )

        price_snapshot = {
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "prices": current_prices,
        }

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                price_snapshot,
                file,
                indent=4,
            )

        temporary_file.replace(
            latest_prices_file
        )

        text = build_paper_dashboard_text(
            self.paper_engine,
            current_prices,
        )

        self.paper_portfolio_text.config(state="normal")
        self.paper_portfolio_text.delete("1.0", tk.END)

        for line in text.splitlines(keepends=True):
            stripped_line = line.strip()
            tag = None

            if stripped_line in {
                "TSX MOMENTUM PRO",
                "PAPER TRADING ANALYTICS",
                "PORTFOLIO",
                "POSITION STATUS",
                "PERFORMANCE",
                "OPEN POSITIONS",
                "RECENT CLOSED TRADES",
            }:
                tag = "heading"

            elif stripped_line.startswith(">>>"):
                tag = "heading"

            elif "Status: PROFIT" in line:
                tag = "profit"

            elif "Status: LOSS" in line:
                tag = "loss"

            elif "Status: FLAT" in line:
                tag = "warning"

            if tag:
                self.paper_portfolio_text.insert(
                    tk.END,
                    line,
                    tag,
                )
            else:
                self.paper_portfolio_text.insert(
                    tk.END,
                    line,
                )

        self.paper_portfolio_text.config(state="disabled")
    
    def update_system_health(self):
        scanner = (
            "REFRESHING"
            if self.is_refreshing
            else "RUNNING"
        )

        execution = (
            "RUNNING"
            if self.automatic_execution_thread.is_alive()
            else "STOPPED"
        )

        eod = (
            "RUNNING"
            if self.automatic_eod_thread.is_alive()
            else "STOPPED"
        )

        monitor = (
            "ACTIVE"
            if self.paper_engine.portfolio.open_positions
            else "WAITING"
        )

        journal = "READY"

        self.system_health_panel.set_status(
            "scanner",
            scanner,
        )

        self.system_health_panel.set_status(
            "execution",
            execution,
        )

        self.system_health_panel.set_status(
            "eod",
            eod,
        )

        self.system_health_panel.set_status(
            "monitor",
            monitor,
        )

        self.system_health_panel.set_status(
            "journal",
            journal,
        )

        self.system_health_panel.update_counts(
            pending_trades=len(
                self.paper_engine.pending_trades.get_all()
            ),
            open_positions=len(
                self.paper_engine.portfolio.open_positions
            ),
            closed_trades=len(
                self.paper_engine.portfolio.closed_trades
            ),
            last_refresh=self.last_successful_refresh,
        )
    def is_mobile_dashboard_running(self, host="127.0.0.1", port=5000):
        """
        Return True when something is already listening on the
        mobile dashboard port.
        """
        try:
            with socket.create_connection(
                (host, port),
                timeout=1.0,
            ):
                return True
        except OSError:
            return False

    def start_mobile_dashboard(self):
        """
        Start the Waitress mobile dashboard unless port 5000
        is already being used.
        """
        if self.is_mobile_dashboard_running():
            print(
                "Mobile dashboard is already running "
                "on port 5000."
            )
            return

        project_root = Path(__file__).resolve().parent.parent

        command = [
            sys.executable,
            "-m",
            "waitress",
            "--listen=0.0.0.0:5000",
            "mobile_dashboard.app:app",
        ]

        startup_info = None
        creation_flags = 0

        if sys.platform == "win32":
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            self.mobile_dashboard_process = subprocess.Popen(
                command,
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startup_info,
                creationflags=creation_flags,
            )

            self.mobile_dashboard_started_here = True

            print(
                "Mobile dashboard started automatically "
                "on port 5000."
            )

        except Exception as error:
            self.mobile_dashboard_process = None
            self.mobile_dashboard_started_here = False

            print(
                "Unable to start mobile dashboard: "
                f"{error}"
            )

    def stop_mobile_dashboard(self):
        """
        Stop the dashboard only when this workstation started it.
        Do not stop an independently running dashboard.
        """
        if not self.mobile_dashboard_started_here:
            return

        process = self.mobile_dashboard_process

        if process is None:
            return

        if process.poll() is not None:
            return

        try:
            process.terminate()
            process.wait(timeout=5)

        except subprocess.TimeoutExpired:
            process.kill()

        except Exception as error:
            print(
                "Unable to stop mobile dashboard cleanly: "
                f"{error}"
            )

        finally:
            self.mobile_dashboard_process = None
            self.mobile_dashboard_started_here = False

    def on_close(self):
        """
        Shut down workstation-owned services and close the GUI.
        """
        self.stop_mobile_dashboard()
        self.root.destroy()
    def update_market_session_status(self):
        session = get_tsx_market_status()

        status = session["status"]
        message = session["message"]

        if status == "OPEN":
            color = "#b6d7a8"
            self.open_paper_trade_button.config(state="normal")
        elif status == "PRE_MARKET":
            color = "#fff2cc"
            self.open_paper_trade_button.config(state="disabled")
        else:
            color = "#f4cccc"
            self.open_paper_trade_button.config(state="disabled")

        self.market_session_label.config(
            text=f"TSX Session: {status} | {message}",
            bg=color,
        )
    def update_countdown(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.update_market_session_status()
        self.update_system_health()
        if self.is_refreshing:
            status = f"Refreshing data... | Time: {now}"
        else:
            status = (
                f"Last Update: {now} | "
                f"Auto-refresh: ON | "
                f"Next refresh in: {self.countdown_seconds}s"
            )

        self.status_label.config(text=status)

        if not self.is_refreshing:
            self.countdown_seconds -= 1

            if self.countdown_seconds <= 0:
                self.refresh_data()

        self.root.after(1000, self.update_countdown)

    def format_percent(self, value):
        if value is None:
            return "N/A"
        return f"{value}%"


def main():
    root = tk.Tk()
    TradingWorkstation(root)
    root.mainloop()


if __name__ == "__main__":
    main()