"""
Northstar Quant
Historical Research Backfill Utility
"""

import csv
import os
import shutil
from datetime import datetime

from paper_trading.journal import (
    FIELDNAMES,
    save_trade,
)
from research.enrichment_engine import enrich_trade


JOURNAL_FILE = "paper_trade_journal.csv"


SIGNAL_DATES = {
    ("BTE.TO", "2026-07-14"): "2026-07-13",
    ("IMO.TO", "2026-07-14"): "2026-07-13",
    ("EQB.TO", "2026-07-16"): "2026-07-15",
    ("DSG.TO", "2026-07-17"): "2026-07-16",
}

def create_fully_enriched_row(row, research):
    """
    Use the production journal writer to flatten every research group.
    """

    temporary_row_path = (
        "paper_trade_journal.backfill_row.tmp.csv"
    )

    if os.path.exists(temporary_row_path):
        os.remove(temporary_row_path)

    trade = dict(row)
    trade["research"] = research

    save_trade(
        trade=trade,
        file_path=temporary_row_path,
    )

    with open(
        temporary_row_path,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        enriched_row = next(reader)

    os.remove(temporary_row_path)

    return enriched_row


def backfill_historical_research(
    file_path=JOURNAL_FILE,
):
    """
    Backfill missing research fields for historical journal rows.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Journal file not found: {file_path}"
        )

    backup_timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        f"{file_path}.before_research_backfill_"
        f"{backup_timestamp}.bak"
    )

    shutil.copy2(
        file_path,
        backup_path,
    )

    with open(
        file_path,
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    updated_count = 0
    skipped_count = 0

    for index, row in enumerate(rows):
        symbol = row.get("symbol", "")
        entry_date = row.get("entry_date", "")

        signal_date = SIGNAL_DATES.get(
            (symbol, entry_date)
        )

        if not signal_date:
            skipped_count += 1
            continue

        research = enrich_trade(
            {
                "symbol": symbol,
                "signal_date": signal_date,
            }
        )

        rows[index] = create_fully_enriched_row(
            row=row,
            research=research,
        )

        updated_count += 1

    temporary_path = f"{file_path}.tmp"

    with open(
        temporary_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)

    os.replace(
        temporary_path,
        file_path,
    )

    print(
        "Historical research backfill complete."
    )

    print(
        f"Updated rows: {updated_count}"
    )

    print(
        f"Skipped rows: {skipped_count}"
    )

    print(
        f"Backup created: {backup_path}"
    )


if __name__ == "__main__":
    backfill_historical_research()