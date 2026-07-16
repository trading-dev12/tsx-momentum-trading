"""
Pending Trade Queue

Stores validated end-of-day READY signals until they can be
executed using an actual next-trading-day entry price.
"""

import csv
import os


PENDING_TRADES_FILE = "pending_trades.csv"


class PendingTradeQueue:
    def __init__(self, file_path=PENDING_TRADES_FILE):
        self.file_path = file_path
        self.pending_trades = []

        self._load_from_csv()

    def add_trade(self, signal):
        if signal.get("decision") != "READY":
            return {
                "success": False,
                "message": "Only READY signals can be added.",
            }

        symbol = signal["symbol"]

        for trade in self.pending_trades:
            if trade["symbol"] == symbol:
                return {
                    "success": False,
                    "message": f"{symbol} is already pending.",
                }

        pending_trade = {
            "symbol": symbol,
            "strategy": signal.get("strategy", "MOMENTUM"),
            "signal_date": signal["signal_date"],
            "signal_close": float(signal["close"]),
            "atr": float(signal["atr"]),
            "tmqs": float(signal["tmqs"]),
            "rvol": float(signal["rvol"]),
            "breakout": signal["breakout"],
            "reason": signal.get("reason", ""),
            "status": "PENDING",
    }

        self.pending_trades.append(pending_trade)
        self._save_to_csv()

        return {
            "success": True,
            "message": f"{symbol} added to pending trades.",
            "trade": pending_trade,
        }

    def get_all(self):
        return list(self.pending_trades)

    def get_trade(self, symbol):
        for trade in self.pending_trades:
            if trade["symbol"] == symbol:
                return trade.copy()

        return None

    def remove_trade(self, symbol):
        for index, trade in enumerate(self.pending_trades):
            if trade["symbol"] == symbol:
                removed_trade = self.pending_trades.pop(index)
                self._save_to_csv()

                return {
                    "success": True,
                    "message": f"{symbol} removed from pending trades.",
                    "trade": removed_trade,
                }

        return {
            "success": False,
            "message": f"{symbol} was not found.",
        }

    def _load_from_csv(self):
        if not os.path.exists(self.file_path):
            return

        with open(
            self.file_path,
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)

            self.pending_trades = []

            for row in reader:
                row["signal_close"] = float(row["signal_close"])
                row["atr"] = float(row["atr"])
                row["tmqs"] = float(row["tmqs"])
                row["rvol"] = float(row["rvol"])

                row.setdefault("strategy", "MOMENTUM")

                self.pending_trades.append(row)

    def _save_to_csv(self):
        fieldnames = [
            "symbol",
            "strategy",
            "signal_date",
            "signal_close",
            "atr",
            "tmqs",
            "rvol",
            "breakout",
            "reason",
            "status",
        ]

        with open(
            self.file_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
            )

            writer.writeheader()
            writer.writerows(self.pending_trades)