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

    # Sector Strength research
    "sector",
    "sector_etf",
    "market_benchmark",
    "sector_return_20",
    "market_return_20",
    "sector_strength_20",
    "sector_status",
    "sector_measurement_date",
    "sector_strength_status",

    # Gap Analysis research
    "previous_close",
    "previous_high",
    "previous_low",
    "signal_open",
    "gap_percent",
    "gap_direction",
    "gap_bucket",
    "open_vs_previous_high_percent",
    "open_vs_previous_low_percent",
    "gap_measurement_date",
    "gap_analysis_status",

    # Volatility Regime research
    "volatility_close",
    "atr_14",
    "atr_percent",
    "realized_volatility_20",
    "volatility_percentile_252",
    "volatility_regime",
    "volatility_measurement_date",
    "volatility_regime_status",

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

def flatten_research_into_row(row, research):
    """
    Flatten research engine output into a journal row.
    """

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
    
    return row


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

    flatten_research_into_row(
        row=row,
        research=research,
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
    # Flatten the Sector Strength research data.
    sector_strength = research.get(
        "sector_strength", {}
    )

    row["sector"] = sector_strength.get(
        "sector", ""
    )

    row["sector_etf"] = sector_strength.get(
        "sector_etf", ""
    )

    row["market_benchmark"] = sector_strength.get(
        "market_benchmark", ""
    )

    row["sector_return_20"] = sector_strength.get(
        "sector_return_20", ""
    )

    row["market_return_20"] = sector_strength.get(
        "market_return_20", ""
    )

    row["sector_strength_20"] = sector_strength.get(
        "sector_strength_20", ""
    )

    row["sector_status"] = sector_strength.get(
        "sector_status", ""
    )

    row["sector_measurement_date"] = sector_strength.get(
        "measurement_date", ""
    )

    row["sector_strength_status"] = sector_strength.get(
        "status", ""
    )

    # Flatten the Gap Analysis research data.
    gap_analysis = research.get(
        "gap_analysis", {}
    )

    row["previous_close"] = gap_analysis.get(
        "previous_close", ""
    )

    row["previous_high"] = gap_analysis.get(
        "previous_high", ""
    )

    row["previous_low"] = gap_analysis.get(
        "previous_low", ""
    )

    row["signal_open"] = gap_analysis.get(
        "signal_open", ""
    )

    row["gap_percent"] = gap_analysis.get(
        "gap_percent", ""
    )

    row["gap_direction"] = gap_analysis.get(
        "gap_direction", ""
    )

    row["gap_bucket"] = gap_analysis.get(
        "gap_bucket", ""
    )

    row["open_vs_previous_high_percent"] = gap_analysis.get(
        "open_vs_previous_high_percent", ""
    )

    row["open_vs_previous_low_percent"] = gap_analysis.get(
        "open_vs_previous_low_percent", ""
    )

    row["gap_measurement_date"] = gap_analysis.get(
        "measurement_date", ""
    )

    row["gap_analysis_status"] = gap_analysis.get(
        "status", ""
    )
     # Flatten the Volatility Regime research data.
    volatility_regime = research.get(
        "volatility_regime", {}
    )

    row["volatility_close"] = volatility_regime.get(
        "close", ""
    )

    row["atr_14"] = volatility_regime.get(
        "atr_14", ""
    )

    row["atr_percent"] = volatility_regime.get(
        "atr_percent", ""
    )

    row["realized_volatility_20"] = volatility_regime.get(
        "realized_volatility_20", ""
    )

    row["volatility_percentile_252"] = volatility_regime.get(
        "volatility_percentile_252", ""
    )

    row["volatility_regime"] = volatility_regime.get(
        "volatility_regime", ""
    )

    row["volatility_measurement_date"] = volatility_regime.get(
        "measurement_date", ""
    )

    row["volatility_regime_status"] = volatility_regime.get(
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