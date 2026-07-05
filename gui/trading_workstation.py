import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading

from core.config_loader import load_settings
from core.watchlist_loader import load_watchlist
from core.market_data import get_quotes
from core.market_context import score_market_context


class TradingWorkstation:
    def __init__(self, root):
        self.root = root
        self.root.title("TSX Momentum Pro")
        self.root.geometry("1200x720")

        self.auto_refresh = True
        self.refresh_interval_seconds = 30
        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False

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

        self.refresh_button = tk.Button(
            root,
            text="Refresh Scanner",
            command=self.refresh_data,
            font=("Arial", 11, "bold"),
        )
        self.refresh_button.pack(padx=10, pady=5, anchor="w")

        columns = (
            "rank",
            "symbol",
            "price",
            "tmqs",
            "rvol",
            "breakout",
            "momentum",
            "liquidity",
            "decision",
        )

        self.tree = ttk.Treeview(root, columns=columns, show="headings")

        headings = {
            "rank": "#",
            "symbol": "Symbol",
            "price": "Price",
            "tmqs": "TMQS",
            "rvol": "RVOL",
            "breakout": "Breakout",
            "momentum": "Momentum",
            "liquidity": "Liquidity",
            "decision": "Decision",
        }

        for column, title in headings.items():
            self.tree.heading(column, text=title)

        self.tree.column("rank", width=50, anchor="center")
        self.tree.column("symbol", width=100, anchor="center")
        self.tree.column("price", width=100, anchor="center")
        self.tree.column("tmqs", width=80, anchor="center")
        self.tree.column("rvol", width=80, anchor="center")
        self.tree.column("breakout", width=160, anchor="center")
        self.tree.column("momentum", width=100, anchor="center")
        self.tree.column("liquidity", width=100, anchor="center")
        self.tree.column("decision", width=120, anchor="center")

        self.tree.tag_configure("READY", background="#b6d7a8")
        self.tree.tag_configure("BUY", background="#b6d7a8")
        self.tree.tag_configure("WATCH", background="#fff2cc")
        self.tree.tag_configure("IGNORE", background="#f4cccc")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

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
            watchlist = load_watchlist(settings["watchlist_file"])

            market = score_market_context()
            quotes = get_quotes(watchlist)

            self.root.after(0, lambda: self.update_dashboard(market, quotes))

        except Exception as error:
            self.root.after(0, lambda: self.show_error(error))

    def update_dashboard(self, market, quotes):
        for row in self.tree.get_children():
            self.tree.delete(row)

        market_status = market["status"]
        market_score = market["score"]

        tsx = self.format_percent(market["tsx_change"])
        oil = self.format_percent(market["oil_change"])
        bitcoin = self.format_percent(market["bitcoin_change"])
        vix = self.format_percent(market["vix_change"])

        self.market_label.config(
            text=(
                f"Market Health: {market_status} | "
                f"Score: {market_score}/100 | "
                f"TSX: {tsx} | Oil: {oil} | "
                f"Bitcoin: {bitcoin} | VIX: {vix}"
            )
        )

        total = len(quotes)
        ready = sum(1 for q in quotes if q["decision"] == "READY")
        watch = sum(1 for q in quotes if q["decision"] == "WATCH")
        ignore = sum(1 for q in quotes if q["decision"] == "IGNORE")
        average_tmqs = sum(q["tmqs"] for q in quotes) / total if total else 0
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

        for rank, quote in enumerate(quotes, start=1):
            decision = quote["decision"]

            self.tree.insert(
                "",
                "end",
                values=(
                    rank,
                    quote["symbol"],
                    f"{quote['price']:.2f}",
                    quote["tmqs"],
                    f"{quote['relative_volume']:.2f}x",
                    quote["breakout_status"],
                    quote["grades"]["Momentum"],
                    quote["grades"]["Liquidity"],
                    decision,
                ),
                tags=(decision,),
            )

        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False

        self.refresh_button.config(state="normal", text="Refresh Scanner")

    def show_error(self, error):
        self.is_refreshing = False
        self.status_label.config(text=f"Error: {error}")
        self.refresh_button.config(state="normal", text="Refresh Scanner")

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