"""
Paper Trading Journal

Saves completed paper trades to a CSV journal.
"""

import csv
import os


JOURNAL_FILE = "paper_trade_journal.csv"


def save_trade(trade, file_path=JOURNAL_FILE):
    file_exists = os.path.exists(file_path)

    fieldnames = [
        "symbol",
        "strategy",
        "entry_date",
        "exit_date",
        "entry_price",
        "exit_price",
        "shares",
        "stop_price",
        "target_price",
        "tmqs",
        "rvol",
        "exit_reason",
        "profit_loss",
        "profit_loss_percent",
    ]

    with open(file_path, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row = {}

        for field in fieldnames:
            row[field] = trade.get(field, "")

        writer.writerow(row)