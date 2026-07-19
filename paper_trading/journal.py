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

        # Relative Strength research
        "stock_return_20",
        "xic_return_20",
        "xiu_return_20",
        "rs_xic_20",
        "rs_xiu_20",
        "rs_measurement_date",
        "rs_status",
    ]

    with open(file_path, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row = {}

        # Copy the existing trade fields
        for field in fieldnames:
            row[field] = trade.get(field, "")

        # Flatten the Relative Strength research data
        rs = (
            trade.get("research", {})
                 .get("relative_strength", {})
        )

        row["stock_return_20"] = rs.get(
            "stock_return_20", ""
        )

        row["xic_return_20"] = rs.get(
            "xic_return_20", ""
        )

        row["xiu_return_20"] = rs.get(
            "xiu_return_20", ""
        )

        row["rs_xic_20"] = rs.get(
            "rs_xic_20", ""
        )

        row["rs_xiu_20"] = rs.get(
            "rs_xiu_20", ""
        )

        row["rs_measurement_date"] = rs.get(
            "measurement_date", ""
        )

        row["rs_status"] = rs.get(
            "status", ""
        )

        writer.writerow(row)