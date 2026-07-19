"""
Paper Trading Journal

Saves completed paper trades to a CSV journal.
"""

import csv
import os


JOURNAL_FILE = "paper_trade_journal.csv"


FIELDNAMES = [
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

    # Market Regime research
    "market_regime",
    "market_regime_benchmark",
    "market_regime_close",
    "market_regime_sma_50",
    "market_regime_sma_200",
    "market_regime_close_vs_sma_200_percent",
    "market_regime_sma_50_vs_sma_200_percent",
    "market_regime_measurement_date",
    "market_regime_status",

     # Moving Average Context research
    "ma_close",
    "ma_sma_20",
    "ma_sma_50",
    "ma_sma_200",
    "ma_close_vs_sma20_percent",
    "ma_close_vs_sma50_percent",
    "ma_close_vs_sma200_percent",
    "ma_sma20_vs_sma50_percent",
    "ma_sma50_vs_sma200_percent",
    "ma_trend_alignment",
    "ma_measurement_date",
    "ma_status",
]


def ensure_journal_schema(file_path, fieldnames):
    """
    Upgrade an existing journal to the current column schema.

    Existing rows are preserved. Newly added columns are left blank
    for historical trades that did not record those research factors.
    """

    if not os.path.exists(file_path):
        return

    if os.path.getsize(file_path) == 0:
        return

    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        existing_fieldnames = reader.fieldnames or []

        if existing_fieldnames == fieldnames:
            return

        existing_rows = list(reader)

    temporary_path = f"{file_path}.tmp"

    with open(
        temporary_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for existing_row in existing_rows:
            upgraded_row = {
                field: existing_row.get(field, "")
                for field in fieldnames
            }

            writer.writerow(upgraded_row)

    os.replace(temporary_path, file_path)


def save_trade(trade, file_path=JOURNAL_FILE):
    ensure_journal_schema(
        file_path=file_path,
        fieldnames=FIELDNAMES,
    )

    file_exists = (
        os.path.exists(file_path)
        and os.path.getsize(file_path) > 0
    )

    row = {}

    # Copy the existing trade fields.
    for field in FIELDNAMES:
        row[field] = trade.get(field, "")

    research = trade.get("research", {})

    # Flatten the Relative Strength research data.
    rs = research.get("relative_strength", {})

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

    # Flatten the Market Regime research data.
    market_regime = research.get(
        "market_regime", {}
    )

    row["market_regime"] = market_regime.get(
        "regime", ""
    )

    row["market_regime_benchmark"] = market_regime.get(
        "benchmark", ""
    )

    row["market_regime_close"] = market_regime.get(
        "benchmark_close", ""
    )

    row["market_regime_sma_50"] = market_regime.get(
        "sma_50", ""
    )

    row["market_regime_sma_200"] = market_regime.get(
        "sma_200", ""
    )

    row[
        "market_regime_close_vs_sma_200_percent"
    ] = market_regime.get(
        "close_vs_sma_200_percent", ""
    )

    row[
        "market_regime_sma_50_vs_sma_200_percent"
    ] = market_regime.get(
        "sma_50_vs_sma_200_percent", ""
    )

    row[
        "market_regime_measurement_date"
    ] = market_regime.get(
        "measurement_date", ""
    )

    row["market_regime_status"] = market_regime.get(
        "status", ""
    )
     # Flatten the Moving Average Context research data.
    moving_average_context = research.get(
        "moving_average_context", {}
    )

    row["ma_close"] = moving_average_context.get(
        "close", ""
    )

    row["ma_sma_20"] = moving_average_context.get(
        "sma_20", ""
    )

    row["ma_sma_50"] = moving_average_context.get(
        "sma_50", ""
    )

    row["ma_sma_200"] = moving_average_context.get(
        "sma_200", ""
    )

    row["ma_close_vs_sma20_percent"] = (
        moving_average_context.get(
            "close_vs_sma20_percent", ""
        )
    )

    row["ma_close_vs_sma50_percent"] = (
        moving_average_context.get(
            "close_vs_sma50_percent", ""
        )
    )

    row["ma_close_vs_sma200_percent"] = (
        moving_average_context.get(
            "close_vs_sma200_percent", ""
        )
    )

    row["ma_sma20_vs_sma50_percent"] = (
        moving_average_context.get(
            "sma20_vs_sma50_percent", ""
        )
    )

    row["ma_sma50_vs_sma200_percent"] = (
        moving_average_context.get(
            "sma50_vs_sma200_percent", ""
        )
    )

    row["ma_trend_alignment"] = moving_average_context.get(
        "trend_alignment", ""
    )

    row["ma_measurement_date"] = moving_average_context.get(
        "measurement_date", ""
    )

    row["ma_status"] = moving_average_context.get(
        "status", ""
    )
    with open(
        file_path,
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)