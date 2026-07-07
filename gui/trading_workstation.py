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
        self.root.geometry("1450x760")

        self.refresh_interval_seconds = 30
        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.latest_quotes = []

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
        self.tree.tag_configure("BUY", background="#b6d7a8")
        self.tree.tag_configure("WATCH", background="#fff2cc")
        self.tree.tag_configure("IGNORE", background="#f4cccc")

        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_trade_checklist)

        checklist_frame = tk.Frame(main_frame, width=320)
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
            width=38,
            height=28,
            font=("Consolas", 10),
            wrap="word",
        )
        self.checklist_text.pack(fill="both", expand=True)
        self.checklist_text.insert("1.0", "Click a stock to view details.")
        self.checklist_text.config(state="disabled")

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
        self.latest_quotes = quotes

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
        best = max(quotes, key=lambda q: q["tmqs"]) if total else None
        best_text = best["symbol"] if best else "N/A"
        if best:
            best_confidence = best.get("confidence_score", 0)
            best_decision = best["decision"]
            best_reason = best.get("reason", "")
            best_rvol = best["relative_volume"]
            best_breakout = best["breakout_status"]
        if best_decision == "READY":
                banner_color = "#b6d7a8"
        elif best_decision == "WATCH":
                banner_color = "#fff2cc"
        else:
                banner_color = "#f4cccc"
        self.best_trade_label.config(
                text=(
                    f"Best Trade Candidate: {best['symbol']} | "
                    f"Decision: {best_decision} | "
                    f"TMQS: {best['tmqs']} | "
                    f"Confidence: {best_confidence}% | "
                    f"RVOL: {best_rvol:.2f}x | "
                    f"Breakout: {best_breakout} | "
                    f"Reason: {best_reason}"
                   ),
                bg=banner_color,
            )
            
        
        self.summary_label.config(
                text=(
                    f"Stocks Scanned: {total} | "
                    f"READY: {ready} | WATCH: {watch} | IGNORE: {ignore} | "
                    f"Average TMQS: {average_tmqs:.1f} | "
                    f"Best Candidate: {best_text}"
                   )
            )

        for rank, quote in enumerate(quotes, start=1):
            

            rvol_grade = quote.get("grades", {}).get("RVOL", "N/A")
            confidence = quote.get("confidence_score", 0)
            decision = quote["decision"]

            if isinstance(decision, tuple):
                decision, reason = decision
            else:
                reason = quote.get("reason", "")
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

        self.countdown_seconds = self.refresh_interval_seconds
        self.is_refreshing = False
        self.refresh_button.config(state="normal", text="Refresh Scanner")

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
        decision_data = quote["decision"]

        if isinstance(decision_data, tuple):
            decision, reason = decision_data
        else:
            decision = decision_data
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