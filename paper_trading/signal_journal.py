from pathlib import Path
import csv

SIGNAL_JOURNAL = Path("paper_signal_journal.csv")

FIELDNAMES = [
    "signal_date",
    "symbol",
    "strategy",
    "decision",
    "close",
    "atr",
    "tmqs",
    "rvol",
    "breakout",
    "reason",
]


def _load_existing_keys():
    if not SIGNAL_JOURNAL.exists():
        return set()

    with SIGNAL_JOURNAL.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return {
            (
                row.get("signal_date", ""),
                row.get("symbol", ""),
                row.get("strategy", ""),
            )
            for row in reader
        }


def record_ready_signals(results, signal_date):
    existing_keys = _load_existing_keys()
    file_exists = SIGNAL_JOURNAL.exists()

    with SIGNAL_JOURNAL.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if not file_exists:
            writer.writeheader()

        for row in results:
            if row.get("decision") != "READY":
                continue

            signal_key = (
                str(signal_date),
                row.get("symbol", ""),
                "MOMENTUM",
            )

            if signal_key in existing_keys:
                continue

            writer.writerow({
                "signal_date": signal_date,
                "symbol": row.get("symbol"),
                "strategy": "MOMENTUM",
                "decision": row.get("decision"),
                "close": row.get("close"),
                "atr": row.get("atr"),
                "tmqs": row.get("tmqs"),
                "rvol": row.get("rvol"),
                "breakout": row.get("breakout"),
                "reason": row.get("reason"),
            })

            existing_keys.add(signal_key)