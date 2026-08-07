import json
import socket
import subprocess
import sys
from pathlib import Path
import logging

from shlex import quote
import tkinter as tk
from core.market_hours import (
    get_tsx_market_status,
    is_tsx_trading_day,
)
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import threading
from core.eod_signal_service import scan_eod_signals

from paper_trading.dashboard import build_paper_dashboard_text
from notifications.telegram_notifier import send_telegram_message
from core.config_loader import load_settings
from core.watchlist_loader import load_all_watchlists
from core.market_data import get_quotes
from core.connectivity_monitor import (
    check_internet_connectivity,
)
from core.connectivity_state import (
    record_connectivity_status,
)
from core.connectivity_recovery_alert import (
    save_pending_recovery_alert,
    try_send_pending_recovery_alert,
)
from core.market_context import score_market_context
from paper_trading.paper_engine import PaperTradingEngine
from paper_trading.automatic_execution import (
    start_automatic_execution_service,
)
from paper_trading.automatic_eod import (
    run_52_week_shadow_scan,
    run_mean_reversion_shadow_scan,
    start_automatic_eod_service,
)
from gui.system_health_panel import (
    SystemHealthPanel,
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_FOLDER = PROJECT_ROOT / "logs"
LOG_FOLDER.mkdir(exist_ok=True)

RUNTIME_FOLDER = PROJECT_ROOT / "data" / "runtime"
RUNTIME_FOLDER.mkdir(parents=True, exist_ok=True)

SCANNER_SNAPSHOT_FILE = (
    RUNTIME_FOLDER / "latest_scanner_snapshot.json"
)

logging.basicConfig(
    filename=LOG_FOLDER / "workstation.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

class TradingWorkstation:
    def __init__(self, root):
        self.notified_ready_symbols = set()
        self.root = root
        self.root.title("Northstar Quant")
        self.root.geometry("1450x760")
        self.current_view = "LIVE"

        self.mobile_dashboard_process = None
        self.mobile_dashboard_started_here = False

        self.start_mobile_dashboard()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_interval_seconds = 300
        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.refresh_timeout_ms = 240_000
        self.refresh_sequence = 0
        self.active_refresh_id = None
        self.latest_quotes = []
        self.previous_ready_symbols = None
        self.last_successful_refresh = None
        self.paper_engine = PaperTradingEngine(
            starting_cash=500000,
            risk_model="fixed",
            fixed_risk_amount=100.0,
            max_open_positions=100,
        )

        self.breakout_52week_engine = PaperTradingEngine(
            starting_cash=500000,
            portfolio_state_file="paper_portfolio_state_52week.json",
            pending_trades_file="pending_trades_52week.csv",
            journal_file="paper_trade_journal_52week.csv",
            risk_model="fixed",
            fixed_risk_amount=100.0,
            max_open_positions=100,
        )

        self.mean_reversion_engine = PaperTradingEngine(
            starting_cash=500000,
            portfolio_state_file="paper_portfolio_state_mean_reversion.json",
            pending_trades_file="pending_trades_mean_reversion.csv",
            journal_file="paper_trade_journal_mean_reversion.csv",
            risk_model="fixed",
            fixed_risk_amount=100.0,
            max_open_positions=100,
        )

        self.automatic_execution_thread = (
            start_automatic_execution_service(
                self.paper_engine,
            )
        )

        self.breakout_52week_execution_thread = (
            start_automatic_execution_service(
                self.breakout_52week_engine,
            )
        )

        self.mean_reversion_execution_thread = (
            start_automatic_execution_service(
                self.mean_reversion_engine,
            )
        )

        self.automatic_eod_thread = (
            start_automatic_eod_service(
                self.paper_engine,
                breakout_52week_engine=self.breakout_52week_engine,
                mean_reversion_engine=self.mean_reversion_engine,
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
            "strategy",
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
            "strategy": "Strategy",
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
        self.tree.column("strategy", width=125, anchor="center")
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
            text="TRADE CONTROL CENTER",
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

        self.update_paper_portfolio_panel()

        self.morning_health_state_file = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "runtime"
            / "morning_health_state.json"
        )
        self.morning_health_in_flight = False
        self.morning_health_sent_date = (
            self.load_morning_health_sent_date()
        )

        startup_session = get_tsx_market_status()

        if startup_session["is_open"]:
            self.refresh_data()
        else:
            snapshot_loaded = self.display_saved_scanner_snapshot()

            snapshot_status = (
                "Last completed scan restored."
                if snapshot_loaded
                else "No saved scanner snapshot available."
            )

            self.status_label.config(
                text=(
                    f"{startup_session['message']} | "
                    "Automatic scanning paused. | "
                    f"{snapshot_status}"
                )
            )




        self.update_countdown()

    def refresh_data(self):
        self.current_view = "LIVE"

        if self.is_refreshing:
            return

        self.refresh_sequence += 1
        refresh_id = self.refresh_sequence

        self.active_refresh_id = refresh_id
        self.is_refreshing = True
        self.write_scanner_health(
            status="REFRESHING",
        )

        logging.info(
            "Scanner refresh %s started",
            refresh_id,
        )

        self.refresh_button.config(
            state="disabled",
            text="Refreshing...",
        )
        self.status_label.config(
            text="Refreshing scanner data...",
        )

        self.root.after(
            self.refresh_timeout_ms,
            lambda rid=refresh_id: (
                self.handle_refresh_timeout(rid)
            ),
        )

        thread = threading.Thread(
            target=self.load_data,
            args=(refresh_id,),
            daemon=True,
        )
        thread.start()

    def handle_refresh_timeout(self, refresh_id):
        if (
            not self.is_refreshing
            or self.active_refresh_id != refresh_id
        ):
            return

        logging.error(
            "Scanner refresh %s timed out after %.1f seconds",
            refresh_id,
            self.refresh_timeout_ms / 1000,
        )

        self.active_refresh_id = None
        self.is_refreshing = False
        self.countdown_seconds = (
            self.refresh_interval_seconds
        )

        self.refresh_button.config(
            state="normal",
            text="Refresh Scanner",
        )
        self.status_label.config(
            text=(
                "Scanner refresh timed out. "
                "The interface has been released and "
                "will try again."
            )
        )

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
                momentum_results = scan_eod_signals()

                breakout_scan = run_52_week_shadow_scan(
                    paper_engine=self.breakout_52week_engine,
                )

                mean_reversion_scan = run_mean_reversion_shadow_scan(
                    paper_engine=self.mean_reversion_engine,
                )

                combined_results = {
                    "ready": [],
                    "watch": [],
                    "ignore": [],
                    "errors": [],
                }

                strategy_results = (
                    momentum_results,
                    breakout_scan["results"],
                    mean_reversion_scan["results"],
                )

                for strategy_result in strategy_results:
                    for decision_group in (
                        "ready",
                        "watch",
                        "ignore",
                    ):
                        combined_results[
                            decision_group
                        ].extend(
                            self.normalize_eod_quote(quote)
                            for quote in strategy_result[
                                decision_group
                            ]
                        )

                    combined_results["errors"].extend(
                        strategy_result.get(
                            "errors",
                            [],
                        )
                    )

                def finish_scan():
                    ready_count = len(
                        combined_results["ready"]
                    )
                    watch_count = len(
                        combined_results["watch"]
                    )
                    ignore_count = len(
                        combined_results["ignore"]
                    )
                    error_count = len(
                        combined_results["errors"]
                    )

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

                    self.display_eod_results(
                        combined_results,
                        momentum_queue_results=(
                            momentum_results
                        ),
                    )
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

    def write_scanner_health(
        self,
        status="RUNNING",
    ):

        """
        Persist scanner heartbeat for the mobile dashboard.
        """

        runtime_folder = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "runtime"
        )

        runtime_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        health_file = (
            runtime_folder
            / "scanner_health.json"
        )

        heartbeat = {
            "status": status,
            "heartbeat": datetime.now().isoformat(),
            "last_successful_refresh":
                self.last_successful_refresh,
            "refresh_id":
                self.refresh_sequence,
            "worker":
                (
                    "RUNNING"
                    if self.is_refreshing
                    else "IDLE"
                ),
        }

        with health_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                heartbeat,
                file,
                indent=4,
            )

    def load_data(self, refresh_id):
        try:
            logging.info(
                "Scanner refresh %s: loading settings",
                refresh_id,
            )
            load_settings()

            logging.info(
                "Scanner refresh %s: loading watchlist",
                refresh_id,
            )
            watchlist = load_all_watchlists()

            logging.info(
                "Scanner refresh %s: loading market context",
                refresh_id,
            )
            market = score_market_context()

            logging.info(
                "Scanner refresh %s: loading momentum quotes",
                refresh_id,
            )
            quotes = get_quotes(watchlist)

            logging.info(
                "Scanner refresh %s: running 52-week scan",
                refresh_id,
            )
            breakout_scan = run_52_week_shadow_scan()

            logging.info(
                "Scanner refresh %s: running mean-reversion scan",
                refresh_id,
            )
            mean_reversion_scan = (
                run_mean_reversion_shadow_scan()
            )

            breakout_quotes = (
                breakout_scan["results"]["ready"]
                + breakout_scan["results"]["watch"]
            )

            mean_reversion_quotes = (
                mean_reversion_scan["results"]["ready"]
                + mean_reversion_scan["results"]["watch"]
            )

            combined_quotes = list(quotes)

            combined_quotes.extend(
                self.normalize_strategy_quote(quote)
                for quote in breakout_quotes
            )

            combined_quotes.extend(
                self.normalize_strategy_quote(quote)
                for quote in mean_reversion_quotes
            )

            logging.info(
                (
                    "Scanner refresh %s completed data loading | "
                    "Momentum: %s | 52-Week: %s | "
                    "Mean Reversion: %s"
                ),
                refresh_id,
                len(quotes),
                len(breakout_quotes),
                len(mean_reversion_quotes),
            )

            self.root.after(
                0,
                lambda rid=refresh_id,
                loaded_market=market,
                loaded_quotes=combined_quotes: (
                    self.finish_refresh_success(
                        rid,
                        loaded_market,
                        loaded_quotes,
                    )
                ),
            )

        except Exception as error:
            logging.exception(
                "Scanner refresh %s failed",
                refresh_id,
            )

            self.root.after(
                0,
                lambda rid=refresh_id,
                caught_error=error: (
                    self.finish_refresh_error(
                        rid,
                        caught_error,
                    )
                ),
            )

    def finish_refresh_success(
        self,
        refresh_id,
        market,
        quotes,
    ):
        if self.active_refresh_id != refresh_id:
            logging.warning(
                "Ignoring stale scanner refresh %s",
                refresh_id,
            )
            return

        try:
            self.update_dashboard(
                market,
                quotes,
            )

            self.active_refresh_id = None

            self.status_label.config(
                text=(
                    "Scanner refresh completed successfully at "
                    f"{datetime.now().strftime('%H:%M:%S')}."
                )
            )

            self.root.after(
                0,
                self.run_position_monitor_safely,
            )

        except Exception as error:
            logging.exception(
                "Scanner refresh %s failed during display",
                refresh_id,
            )

            self.finish_refresh_error(
                refresh_id,
                error,
            )

    def finish_refresh_error(
        self,
        refresh_id,
        error,
    ):
        if self.active_refresh_id != refresh_id:
            logging.warning(
                "Ignoring stale scanner error from refresh %s",
                refresh_id,
            )
            return

        self.active_refresh_id = None
        self.show_error(error)

    def run_position_monitor_safely(self):
        try:
            self.monitor_paper_positions()
        except Exception:
            logging.exception(
                "Position monitoring failed after scanner refresh"
            )
    def display_saved_scanner_snapshot(self):
        snapshot = self.load_scanner_snapshot()

        if snapshot is None:
            return False

        quotes = snapshot["quotes"]
        generated_at = snapshot["generated_at"].replace(
            "T",
            " ",
        )
        view = snapshot["view"]

        self.latest_quotes = quotes
        self.current_view = f"SAVED_{view}"

        for row in self.tree.get_children():
            self.tree.delete(row)

        total = len(quotes)
        ready = sum(
            1
            for quote in quotes
            if quote.get("decision") == "READY"
        )
        watch = sum(
            1
            for quote in quotes
            if quote.get("decision") == "WATCH"
        )
        ignore = sum(
            1
            for quote in quotes
            if quote.get("decision") == "IGNORE"
        )

        average_tmqs = (
            sum(
                float(quote.get("tmqs", 0) or 0)
                for quote in quotes
            )
            / total
            if total
            else 0
        )

        ready_quotes = [
            quote
            for quote in quotes
            if quote.get("decision") == "READY"
        ]
        watch_quotes = [
            quote
            for quote in quotes
            if quote.get("decision") == "WATCH"
        ]

        candidates = (
            ready_quotes
            or watch_quotes
            or quotes
        )

        best = (
            max(
                candidates,
                key=lambda quote: float(
                    quote.get("tmqs", 0) or 0
                ),
            )
            if candidates
            else None
        )

        self.market_label.config(
            text=(
                "Market Health: Market Closed | "
                f"Showing saved {view} scan from "
                f"{generated_at}"
            )
        )

        queue_line, existing_line = (
            self.build_strategy_queue_summary(
                ready_quotes
            )
        )

        self.summary_label.config(
            text=(
                f"Saved {view} Scan | {queue_line}\n"
                f"{existing_line} | "
                f"READY: {ready} | "
                f"WATCH: {watch} | "
                f"IGNORE: {ignore} | "
                f"Average TMQS: {average_tmqs:.1f}"
            )
        )

        if best:
            best_rvol = float(
                best.get(
                    "relative_volume",
                    best.get("rvol", 0),
                )
                or 0
            )
            best_breakout = best.get(
                "breakout_status",
                best.get("breakout", "N/A"),
            )
            decision = best.get(
                "decision",
                "IGNORE",
            )

            if decision == "READY":
                banner_color = "#b6d7a8"
            elif decision == "WATCH":
                banner_color = "#fff2cc"
            else:
                banner_color = "#f4cccc"

            self.best_trade_label.config(
                text=(
                    f"Saved Best Candidate: "
                    f"{best.get('symbol', 'N/A')} | "
                    f"Decision: {decision} | "
                    f"TMQS: {best.get('tmqs', 0)} | "
                    f"RVOL: {best_rvol:.2f}x | "
                    f"Breakout: {best_breakout} | "
                    f"Reason: {best.get('reason', '')}"
                ),
                bg=banner_color,
            )

        for rank, quote in enumerate(
            quotes,
            start=1,
        ):
            decision = quote.get(
                "decision",
                "IGNORE",
            )
            grades = quote.get("grades", {})
            price = float(
                quote.get(
                    "close",
                    quote.get("price", 0),
                )
                or 0
            )
            rvol = float(
                quote.get(
                    "relative_volume",
                    quote.get("rvol", 0),
                )
                or 0
            )
            breakout = quote.get(
                "breakout_status",
                quote.get("breakout", "N/A"),
            )

            self.tree.insert(
                "",
                "end",
                iid=str(rank - 1),
                values=(
                    rank,
                    quote.get("symbol", "N/A"),
                    quote.get("strategy", "MOMENTUM"),
                    f"{price:.2f}",
                    quote.get("tmqs", 0),
                    f"{quote.get('confidence_score', 0)}%",
                    f"{rvol:.2f}x",
                    grades.get("RVOL", "N/A"),
                    breakout,
                    grades.get("Momentum", "N/A"),
                    grades.get("Liquidity", "N/A"),
                    decision,
                    quote.get("reason", ""),
                ),
                tags=(decision,),
            )

        self.update_paper_portfolio_panel()
        return True

    def load_scanner_snapshot(self):
        if not SCANNER_SNAPSHOT_FILE.exists():
            return None

        try:
            with open(
                SCANNER_SNAPSHOT_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                snapshot = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            logging.warning(
                "Could not load scanner snapshot: %s",
                error,
            )
            return None

        quotes = snapshot.get("quotes", [])

        if not isinstance(quotes, list):
            return None

        quotes = [
            quote
            for quote in quotes
            if isinstance(quote, dict)
        ]

        if not quotes:
            return None

        return {
            "generated_at": snapshot.get(
                "generated_at",
                "Unknown",
            ),
            "view": snapshot.get("view", "LIVE"),
            "quotes": quotes,
        }

    def save_scanner_snapshot(self, quotes, view):
        if not quotes:
            return

        def make_json_safe(value):
            if isinstance(value, dict):
                return {
                    str(key): make_json_safe(item)
                    for key, item in value.items()
                }

            if isinstance(value, (list, tuple, set)):
                return [
                    make_json_safe(item)
                    for item in value
                ]

            if hasattr(value, "item"):
                try:
                    return value.item()
                except (TypeError, ValueError):
                    pass

            if value is None or isinstance(
                value,
                (str, int, float, bool),
            ):
                return value

            return str(value)

        snapshot = {
            "generated_at": datetime.now().isoformat(
                timespec="seconds"
            ),
            "view": view,
            "quotes": make_json_safe(quotes),
        }

        temporary_file = SCANNER_SNAPSHOT_FILE.with_suffix(
            ".tmp"
        )

        with open(
            temporary_file,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                snapshot,
                file,
                indent=4,
            )

        temporary_file.replace(
            SCANNER_SNAPSHOT_FILE
        )

    def normalize_eod_quote(self, quote):
        strategy = quote.get(
            "strategy",
            "MOMENTUM",
        )

        price = float(
            quote.get(
                "price",
                quote.get("close", 0),
            )
            or 0
        )

        rvol = float(
            quote.get(
                "rvol",
                quote.get("relative_volume", 0),
            )
            or 0
        )

        breakout = quote.get(
            "breakout",
            quote.get("breakout_status", "N/A"),
        )

        if strategy == "MEAN_REVERSION":
            rsi_2 = float(
                quote.get("rsi_2", 0)
                or 0
            )
            breakout = f"RSI-2: {rsi_2:.1f}"

        return {
            "symbol": quote.get("symbol", "UNKNOWN"),
            "strategy": strategy,
            "decision": quote.get(
                "decision",
                "IGNORE",
            ),
            "reason": quote.get("reason", ""),
            "price": price,
            "close": price,
            "atr": float(
                quote.get("atr", 0)
                or 0
            ),
            "tmqs": float(
                quote.get("tmqs", 0)
                or 0
            ),
            "rvol": rvol,
            "breakout": breakout,
            "signal_date": quote.get(
                "signal_date",
                datetime.now().strftime("%Y-%m-%d"),
            ),
        }

    def build_strategy_queue_summary(self, ready_quotes):
        strategy_engines = (
            ("MOMENTUM", "Momentum", self.paper_engine),
            (
                "52_WEEK_BREAKOUT",
                "52-Week",
                self.breakout_52week_engine,
            ),
            (
                "MEAN_REVERSION",
                "Mean Reversion",
                self.mean_reversion_engine,
            ),
        )

        queue_parts = []
        existing_parts = []

        for strategy, label, engine in strategy_engines:
            pending_count = len(
                engine.pending_trades.get_all()
            )
            queue_parts.append(
                f"{label} Queued: {pending_count}"
            )

            open_symbols = {
                position.get("symbol")
                for position in (
                    engine.portfolio.open_positions
                )
            }

            ready_symbols = {
                quote.get("symbol")
                for quote in ready_quotes
                if quote.get(
                    "strategy",
                    "MOMENTUM",
                ) == strategy
            }

            existing_symbols = sorted(
                symbol
                for symbol in (
                    open_symbols & ready_symbols
                )
                if symbol
            )

            if existing_symbols:
                existing_parts.append(
                    f"{label}: "
                    + ", ".join(existing_symbols)
                )

        queue_line = " | ".join(queue_parts)
        existing_line = (
            "Existing READY Positions: "
            + (
                " | ".join(existing_parts)
                if existing_parts
                else "None"
            )
        )

        return queue_line, existing_line

    def display_eod_results(
        self,
        results,
        momentum_queue_results=None,
    ):
        self.current_view = "EOD"

        eod_quotes = results["ready"] + results["watch"]

        queue_results = (
            momentum_queue_results
            if momentum_queue_results is not None
            else results
        )

        queue_summary = self.paper_engine.queue_eod_signals(
            queue_results
        )

        print(
            (
            "Queued "
            f"{queue_summary['added']} READY signals "
            f"({queue_summary['rejected']} duplicates)."
            )
        )
        self.latest_quotes = eod_quotes
        self.save_scanner_snapshot(
            eod_quotes,
            "EOD",
        )

        for row in self.tree.get_children():
            self.tree.delete(row)

        queue_line, existing_line = (
            self.build_strategy_queue_summary(
                results["ready"]
            )
        )

        self.summary_label.config(
            text=(
                f"{queue_line}\n"
                f"{existing_line} | "
                f"READY: {len(results['ready'])} | "
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
                    quote.get("strategy", "MOMENTUM"),
                    f"{float(
                        quote.get(
                            "price",
                            quote.get("close", 0),
                        )
                        or 0
                    ):.2f}",
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
    def normalize_strategy_quote(self, quote):
        strategy = quote.get("strategy", "MOMENTUM")
        price = float(
            quote.get(
                "price",
                quote.get("close", 0),
            )
            or 0
        )

        if strategy == "52_WEEK_BREAKOUT":
            return {
                "symbol": quote["symbol"],
                "strategy": strategy,
                "price": price,
                "close": price,
                "tmqs": float(quote.get("tmqs", 0) or 0),
                "confidence_score": 0,
                "relative_volume": float(
                    quote.get("rvol", 0) or 0
                ),
                "grades": {
                    "RVOL": "N/A",
                    "Momentum": "N/A",
                    "Liquidity": "N/A",
                },
                "breakout_status": (
                    "52-WEEK BREAKOUT"
                    if quote.get("breakout")
                    else "BELOW 52-WEEK HIGH"
                ),
                "decision": quote["decision"],
                "reason": quote.get("reason", ""),
            }

        if strategy == "MEAN_REVERSION":
            return {
                "symbol": quote["symbol"],
                "strategy": strategy,
                "price": price,
                "close": price,
                "tmqs": 0.0,
                "confidence_score": 0,
                "relative_volume": 0.0,
                "grades": {
                    "RVOL": "N/A",
                    "Momentum": "N/A",
                    "Liquidity": "N/A",
                },
                "breakout_status": (
                    f"RSI-2: "
                    f"{float(quote.get('rsi_2', 0) or 0):.1f}"
                ),
                "decision": quote["decision"],
                "reason": quote.get("reason", ""),
            }

        normalized = dict(quote)
        normalized.setdefault("strategy", "MOMENTUM")
        normalized.setdefault("price", price)
        normalized.setdefault("close", price)
        return normalized

    def update_dashboard(self, market, quotes):
        self.latest_quotes = quotes
        self.save_scanner_snapshot(
            quotes,
            "LIVE",
        )
        self.last_successful_refresh = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.write_scanner_health(
            status="RUNNING",
        )

        self.check_ready_alerts(quotes)


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
        ready = sum(
            1 for quote in quotes
            if quote["decision"] == "READY"
        )
        watch = sum(
            1 for quote in quotes
            if quote["decision"] == "WATCH"
        )
        ignore = sum(
            1 for quote in quotes
            if quote["decision"] == "IGNORE"
        )

        average_tmqs = (
            sum(
                float(quote.get("tmqs", 0) or 0)
                for quote in quotes
            )
            / total
            if total
            else 0
        )

        ready_quotes = [
            quote for quote in quotes
            if quote["decision"] == "READY"
        ]
        watch_quotes = [
            quote for quote in quotes
            if quote["decision"] == "WATCH"
        ]

        if ready_quotes:
            best = max(
                ready_quotes,
                key=lambda quote: float(
                    quote.get("tmqs", 0) or 0
                ),
            )
        elif watch_quotes:
            best = max(
                watch_quotes,
                key=lambda quote: float(
                    quote.get("tmqs", 0) or 0
                ),
            )
        else:
            best = (
                max(
                    quotes,
                    key=lambda quote: float(
                        quote.get("tmqs", 0) or 0
                    ),
                )
                if total
                else None
            )

        best_text = best["symbol"] if best else "N/A"

        self.summary_label.config(
            text=(
                f"Stocks Scanned: {total} | "
                f"READY: {ready} | "
                f"WATCH: {watch} | "
                f"IGNORE: {ignore} | "
                f"Average TMQS: {average_tmqs:.1f} | "
                f"Best Candidate: {best_text}"
            )
        )

        self.update_best_trade_banner(best)

        for rank, quote in enumerate(quotes, start=1):
            decision = quote["decision"]
            reason = quote.get("reason", "")
            grades = quote.get("grades", {})
            rvol_grade = grades.get("RVOL", "N/A")
            confidence = quote.get("confidence_score", 0)
            price = float(
                quote.get(
                    "close",
                    quote.get("price", 0),
                )
                or 0
            )

            self.tree.insert(
                "",
                "end",
                iid=str(rank - 1),
                values=(
                    rank,
                    quote["symbol"],
                    quote.get("strategy", "MOMENTUM"),
                    f"{price:.2f}",
                    quote.get("tmqs", 0),
                    f"{confidence}%",
                    f"{float(quote.get('relative_volume', 0) or 0):.2f}x",
                    rvol_grade,
                    quote.get("breakout_status", "N/A"),
                    grades.get("Momentum", "N/A"),
                    grades.get("Liquidity", "N/A"),
                    decision,
                    reason,
                ),
                tags=(decision,),
            )

        self.update_paper_portfolio_panel()

        self.countdown_seconds = self.refresh_interval_seconds

        self.is_refreshing = False

        self.write_scanner_health(
            status="RUNNING",
        )

        self.refresh_button.config(
            state="normal",
            text="Refresh Scanner",
        )

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
                "NORTHSTAR QUANT - NEW READY ALERT",
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

        print(
            f"Monitoring "
            f"{len(self.paper_engine.portfolio.open_positions)} "
            f"open positions"
        )

        for position in self.paper_engine.portfolio.open_positions:
            print(
                position["symbol"],
                position["symbol"] in current_prices,
            )

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

        open_position_symbols = {
            position["symbol"]
            for engine in (
                self.paper_engine,
                self.breakout_52week_engine,
                self.mean_reversion_engine,
            )
            for position in engine.portfolio.open_positions
        }

        missing_symbols = sorted(
            symbol
            for symbol in open_position_symbols
            if symbol not in current_prices
        )

        if missing_symbols:
            try:
                portfolio_quotes = get_quotes(missing_symbols)

                for quote_data in portfolio_quotes:
                    symbol = quote_data.get("symbol")
                    price = quote_data.get(
                        "price",
                        quote_data.get("close"),
                    )

                    if symbol and price is not None:
                        current_prices[symbol] = float(price)

                logging.info(
                    "Loaded portfolio prices for %s missing open positions",
                    len(missing_symbols),
                )

            except Exception:
                logging.exception(
                    "Could not load prices for missing open positions: %s",
                    ", ".join(missing_symbols),
                )

        for quote_data in self.latest_quotes:
            symbol = quote_data.get("symbol")
            price = quote_data.get(
                "price",
                quote_data.get("close"),
            )

            if symbol and price is not None:
                current_prices[symbol] = float(price)

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

        if current_prices:
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

        elif latest_prices_file.exists():
            try:
                with latest_prices_file.open(
                    "r",
                    encoding="utf-8",
                ) as file:
                    saved_snapshot = json.load(file)

                saved_prices = saved_snapshot.get(
                    "prices",
                    {},
                )

                if saved_prices:
                    current_prices = {
                        symbol: float(price)
                        for symbol, price in saved_prices.items()
                    }

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ) as error:
                logging.warning(
                    "Could not load saved price snapshot: %s",
                    error,
                )

        momentum_text = build_paper_dashboard_text(
            self.paper_engine,
            current_prices,
        )

        breakout_52week_text = build_paper_dashboard_text(
            self.breakout_52week_engine,
            current_prices,
        )

        mean_reversion_text = build_paper_dashboard_text(
            self.mean_reversion_engine,
            current_prices,
        )

        text = (
            ">>> MOMENTUM STRATEGY <<<\n"
            + momentum_text
            + "\n\n>>> 52-WEEK BREAKOUT STRATEGY <<<\n"
            + breakout_52week_text
            + "\n\n>>> MEAN REVERSION STRATEGY <<<\n"
            + mean_reversion_text
        )

        self.paper_portfolio_text.config(state="normal")
        self.paper_portfolio_text.delete("1.0", tk.END)

        for line in text.splitlines(keepends=True):
            stripped_line = line.strip()
            tag = None

            if stripped_line in {
                "NORTHSTAR QUANT",
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

        strategy_engines = (
            self.paper_engine,
            self.breakout_52week_engine,
            self.mean_reversion_engine,
        )

        self.system_health_panel.update_counts(
            pending_trades=sum(
                len(engine.pending_trades.get_all())
                for engine in strategy_engines
            ),
            open_positions=sum(
                len(engine.portfolio.open_positions)
                for engine in strategy_engines
            ),
            closed_trades=sum(
                len(engine.portfolio.closed_trades)
                for engine in strategy_engines
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
        elif status == "PRE-MARKET":
            color = "#fff2cc"
            self.open_paper_trade_button.config(state="disabled")
        else:
            color = "#f4cccc"
            self.open_paper_trade_button.config(state="disabled")

        self.market_session_label.config(
            text=f"TSX Session: {status} | {message}",
            bg=color,
        )

        return session

    def load_morning_health_sent_date(self):
        try:
            if not self.morning_health_state_file.exists():
                return None

            state = json.loads(
                self.morning_health_state_file.read_text(
                    encoding="utf-8"
                )
            )
            return state.get("last_sent_date")

        except Exception:
            logging.exception(
                "Unable to read morning health state"
            )
            return None

    def save_morning_health_sent_date(self, sent_date):
        try:
            self.morning_health_state_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            temporary_file = (
                self.morning_health_state_file.with_name(
                    self.morning_health_state_file.name
                    + ".tmp"
                )
            )

            temporary_file.write_text(
                json.dumps(
                    {
                        "last_sent_date": sent_date,
                    },
                    indent=4,
                ),
                encoding="utf-8",
            )

            temporary_file.replace(
                self.morning_health_state_file
            )

        except Exception:
            logging.exception(
                "Unable to save morning health state"
            )

    def build_morning_health_message(self, now, session):
        engines = (
            (
                "Momentum",
                self.paper_engine,
                self.automatic_execution_thread,
            ),
            (
                "52-Week",
                self.breakout_52week_engine,
                self.breakout_52week_execution_thread,
            ),
            (
                "Mean Reversion",
                self.mean_reversion_engine,
                self.mean_reversion_execution_thread,
            ),
        )

        all_execution_running = all(
            execution_thread.is_alive()
            for _, _, execution_thread in engines
        )

        eod_running = self.automatic_eod_thread.is_alive()

        pipeline_status = (
            "HEALTHY"
            if all_execution_running and eod_running
            else "ATTENTION REQUIRED"
        )

        lines = [
            "Northstar Quant - 9:00 AM System Check",
            "",
            f"Date: {now.strftime('%Y-%m-%d')}",
            f"Time: {now.strftime('%H:%M:%S')}",
            "",
            f"Pipeline: {pipeline_status}",
            "Telegram: CONNECTED - message received",
            (
                "Scanner: "
                + (
                    "REFRESHING"
                    if self.is_refreshing
                    else "READY"
                )
            ),
            (
                "Automatic EOD: "
                + (
                    "RUNNING"
                    if eod_running
                    else "STOPPED"
                )
            ),
            (
                "Last Successful Refresh: "
                + (
                    self.last_successful_refresh
                    or "No live refresh yet"
                )
            ),
            "",
            (
                f"TSX Status: "
                f"{session.get('status', 'UNKNOWN')}"
            ),
            f"Market Info: {session.get('message', '')}",
            "",
        ]

        for label, engine, execution_thread in engines:
            lines.extend(
                [
                    (
                        f"{label} Execution: "
                        + (
                            "RUNNING"
                            if execution_thread.is_alive()
                            else "STOPPED"
                        )
                    ),
                    (
                        f"{label} Pending: "
                        f"{len(engine.pending_trades.get_all())}"
                    ),
                    (
                        f"{label} Open: "
                        f"{len(engine.portfolio.open_positions)}"
                    ),
                ]
            )

        total_pending = sum(
            len(engine.pending_trades.get_all())
            for _, engine, _ in engines
        )

        total_open = sum(
            len(engine.portfolio.open_positions)
            for _, engine, _ in engines
        )

        lines.extend(
            [
                "",
                f"Total Pending Trades: {total_pending}",
                f"Total Open Positions: {total_open}",
            ]
        )

        return "\n".join(lines)

    def send_morning_health_telegram(self, now, session):
        if self.morning_health_in_flight:
            return

        self.morning_health_in_flight = True
        sent_date = now.date().isoformat()
        message = self.build_morning_health_message(
            now,
            session,
        )

        def worker():
            try:
                result = send_telegram_message(message)

                if result.get("success"):
                    self.morning_health_sent_date = sent_date
                    self.save_morning_health_sent_date(
                        sent_date
                    )
                    print(
                        "Morning system-health Telegram "
                        "message sent successfully."
                    )
                else:
                    print(
                        "Morning system-health Telegram "
                        "warning: "
                        f"{result.get('message', '')}"
                    )

            except Exception as error:
                print(
                    "Unexpected morning system-health "
                    f"Telegram error: {error}"
                )

            finally:
                self.morning_health_in_flight = False

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def check_morning_health_telegram(
        self,
        now,
        session,
    ):
        if not is_tsx_trading_day(now.date()):
            return

        if now.hour != 9:
            return

        today = now.date().isoformat()

        if self.morning_health_sent_date == today:
            return

        self.send_morning_health_telegram(
            now,
            session,
        )

    def start_connectivity_check_if_due(self):
        """
        Run the external internet check in a background thread.

        Connectivity is checked at most once every 30 seconds.
        Outage state is persisted locally and recovery Telegram
        notifications are retried until successfully delivered.
        """

        if getattr(
            self,
            "connectivity_check_in_flight",
            False,
        ):
            return

        now = datetime.now()

        last_started = getattr(
            self,
            "last_connectivity_check_started",
            None,
        )

        if last_started is not None:
            elapsed_seconds = (
                now - last_started
            ).total_seconds()

            if elapsed_seconds < 30:
                return

        self.connectivity_check_in_flight = True
        self.last_connectivity_check_started = now

        def worker():
            try:
                result = (
                    check_internet_connectivity()
                )

                self.internet_connectivity_result = (
                    result
                )

                online = result.get(
                    "online"
                )

                if not isinstance(
                    online,
                    bool,
                ):
                    return

                try:
                    transition = (
                        record_connectivity_status(
                            online
                        )
                    )

                    self.internet_connectivity_transition = (
                        transition
                    )

                    if (
                        transition.get(
                            "transition"
                        )
                        == "RECOVERED"
                    ):
                        save_pending_recovery_alert(
                            transition
                        )

                    if online:
                        alert_result = (
                            try_send_pending_recovery_alert()
                        )

                        self.connectivity_recovery_alert_result = (
                            alert_result
                        )

                except Exception as error:
                    logging.exception(
                        "Connectivity transition handling "
                        "failed"
                    )

                    self.connectivity_transition_error = (
                        str(error)
                    )

            except Exception as error:
                logging.exception(
                    "Internet connectivity check failed"
                )

                self.internet_connectivity_result = {
                    "online": None,
                    "reachable_target": None,
                    "failures": [],
                    "error": str(error),
                }

            finally:
                self.connectivity_check_in_flight = (
                    False
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()


    def update_countdown(self):
        try:
            now = datetime.now()
            heartbeat = now.strftime("%H:%M:%S")

            session = self.update_market_session_status()
            self.update_system_health()
            self.check_morning_health_telegram(
                now,
                session,
            )

            self.start_connectivity_check_if_due()

            connectivity_result = getattr(
                self,
                "internet_connectivity_result",
                None,
            )

            if connectivity_result is None:
                internet_status = "CHECKING"

            elif connectivity_result.get(
                "online"
            ) is True:
                internet_status = "ONLINE"

            elif connectivity_result.get(
                "online"
            ) is False:
                internet_status = "OFFLINE"

            else:
                internet_status = "UNKNOWN"

            refresh_id = (
                self.active_refresh_id
                if self.active_refresh_id is not None
                else "--"
            )

            worker_state = (
                "RUNNING"
                if self.is_refreshing
                else "IDLE"
            )

            last_success = (
                self.last_successful_refresh
                or "--"
            )

            diagnostics = (
                f"Heartbeat: {heartbeat} | "
                f"Refresh ID: {refresh_id} | "
                f"Worker: {worker_state} | "
                f"Internet: {internet_status} | "
                f"Last Success: {last_success} | "
                f"Countdown: {self.countdown_seconds}s"
            )

            if self.is_refreshing:
                status = (
                    f"{diagnostics} | "
                    "Refreshing scanner data..."
                )

            elif not session["is_open"]:
                self.countdown_seconds = (
                    self.refresh_interval_seconds
                )

                status = (
                    f"{diagnostics} | "
                    "Automatic scanning: PAUSED | "
                    f"{session['message']}"
                )

            elif internet_status == "OFFLINE":
                status = (
                    f"{diagnostics} | "
                    "Internet outage detected | "
                    "Automatic recovery monitoring: ON"
                )

            else:
                status = (
                    f"{diagnostics} | "
                    "Auto-refresh: ON"
                )

            self.status_label.config(
                text=status
            )

            if (
                session["is_open"]
                and not self.is_refreshing
            ):
                self.countdown_seconds -= 1

                if self.countdown_seconds <= 0:
                    self.refresh_data()

        except Exception:
            logging.exception(
                "Countdown and automatic refresh "
                "loop encountered an error"
            )

            try:
                self.status_label.config(
                    text=(
                        "Automatic refresh recovered "
                        "from an error. "
                        "See log for details."
                    )
                )

            except tk.TclError:
                return

        finally:
            try:
                self.root.after(
                    1000,
                    self.update_countdown,
                )

            except tk.TclError:
                pass

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
