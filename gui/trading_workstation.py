import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import threading

from paper_trading.dashboard import build_paper_dashboard_text
from core.config_loader import load_settings
from core.watchlist_loader import load_all_watchlists
from core.market_data import get_quotes
from core.market_context import score_market_context
from paper_trading.paper_engine import PaperTradingEngine

class TradingWorkstation:
    def __init__(self, root):
        self.root = root
        self.root.title("TSX Momentum Pro")
        self.root.geometry("1450x760")

        self.refresh_interval_seconds = 30
        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.latest_quotes = []
        self.previous_ready_symbols = set()
        self.paper_engine = PaperTradingEngine(starting_cash=10000)
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

        self.refresh_button = tk.Button(
            root,
            text="Refresh Scanner",
            command=self.refresh_data,
            font=("Arial", 11, "bold"),
        )
        self.refresh_button.pack(padx=10, pady=5, anchor="w")

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
            font=("Consolas", 10),
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

        portfolio_title = tk.Label(
            checklist_frame,
            text="Paper Portfolio",
            font=("Arial", 14, "bold"),
            anchor="w",
        )
        portfolio_title.pack(fill="x", pady=(8, 5))

        self.paper_portfolio_text = tk.Text(
            checklist_frame,
            width=48,
            height=22,
            font=("Consolas", 10),
            wrap="word",
        )
        self.paper_portfolio_text.pack(fill="both", expand=True)
        self.paper_portfolio_text.config(state="disabled")
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
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.refresh_button.config(state="disabled", text="Refreshing...")
        self.status_label.config(text="Refreshing data...")

        thread = threading.Thread(target=self.load_data)
        thread.daemon = True
        thread.start()

    def load_data(self):
        try:
            settings = load_settings()
            watchlist = load_all_watchlists()
            market = score_market_context()
            quotes = get_quotes(watchlist)

            self.root.after(
                0,
                lambda: self.update_dashboard(market, quotes),
            )

        except Exception as error:
            self.root.after(
                0,
                lambda error=error: self.show_error(error),
            )

    def update_dashboard(self, market, quotes):
        self.latest_quotes = quotes
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

        new_ready_symbols = current_ready_symbols - self.previous_ready_symbols

        if new_ready_symbols:
            print("NEW READY ALERT:", ", ".join(new_ready_symbols))

        self.previous_ready_symbols = current_ready_symbols

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

        rvol_check = "PASS" if rvol >= 0.75 else "FAIL"
        breakout_check = "PASS" if breakout in ["BREAKOUT", "NEAR BREAKOUT"] else "FAIL"
        momentum_check = "PASS" if momentum in ["A", "B"] else "FAIL"
        liquidity_check = "PASS" if liquidity in ["A", "B"] else "FAIL"

        return (
            f"{symbol}\n"
            f"{'-' * 32}\n"
            f"Price:        {price:.2f}\n"
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

        signal = {
            "symbol": symbol,
            "price": price,
            "decision": quote["decision"],
            "tmqs": quote["tmqs"],
            "rvol": quote["relative_volume"],
            "reason": quote.get("reason", ""),
            "shares": shares,
        }

        confirm = messagebox.askyesno(
            "Open Paper Trade",
            (
                f"Open paper trade for {symbol}?\n\n"
                f"Price: ${price:.2f}\n"
                f"Shares: {shares}\n"
                f"Position Cost: ${actual_cost:,.2f}\n"
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
            messagebox.showinfo(
                "Paper Trade Closed",
                (
                    f"{trade['symbol']} was closed automatically.\n\n"
                    f"Exit Price: ${trade['exit_price']:.2f}\n"
                    f"Reason: {trade['exit_reason']}\n"
                    f"Profit/Loss: ${trade['profit_loss']:.2f}\n"
                    f"Return: {trade['profit_loss_percent']:.2f}%"
                ),
            )
    def update_paper_portfolio_panel(self):
        current_prices = {}

        for quote in self.latest_quotes:
            current_prices[quote["symbol"]] = quote["price"]

        text = build_paper_dashboard_text(
            self.paper_engine,
            current_prices,
        )

        self.paper_portfolio_text.config(state="normal")
        self.paper_portfolio_text.delete("1.0", tk.END)
        self.paper_portfolio_text.insert("1.0", text)
        self.paper_portfolio_text.config(state="disabled")
    def update_countdown(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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