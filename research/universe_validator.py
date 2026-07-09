"""
Research Universe Validator

Checks that every symbol in the watchlists has usable historical data.
"""

import os
import glob
import csv


WATCHLIST_FOLDER = "watchlists"
HISTORICAL_FOLDER = "data/historical"
MIN_ROWS_REQUIRED = 200


def symbol_to_filename(symbol):
    return symbol.replace(".", "_") + ".csv"


def get_watchlist_symbols():
    symbols = set()

    files = glob.glob(os.path.join(WATCHLIST_FOLDER, "*.csv"))

    for file in files:
        with open(file, "r") as f:
            reader = csv.reader(f)

            for row in reader:
                if not row:
                    continue

                symbol = row[0].strip()

                if symbol and symbol.upper() != "SYMBOL":
                    symbols.add(symbol)

    return sorted(symbols)


def count_csv_rows(file_path):
    try:
        with open(file_path, "r") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def validate_universe():
    symbols = get_watchlist_symbols()

    valid = []
    missing = []
    too_short = []

    print("=" * 60)
    print("RESEARCH UNIVERSE VALIDATOR")
    print("=" * 60)

    for symbol in symbols:
        filename = symbol_to_filename(symbol)
        path = os.path.join(HISTORICAL_FOLDER, filename)

        if not os.path.exists(path):
            missing.append(symbol)
            continue

        row_count = count_csv_rows(path)

        if row_count < MIN_ROWS_REQUIRED:
            too_short.append((symbol, row_count))
            continue

        valid.append((symbol, row_count))

    print(f"Symbols checked : {len(symbols)}")
    print(f"Valid files     : {len(valid)}")
    print(f"Missing files   : {len(missing)}")
    print(f"Too short files : {len(too_short)}")

    if missing:
        print("\nMISSING FILES")
        print("-" * 60)
        for symbol in missing:
            print(symbol)

    if too_short:
        print("\nTOO SHORT FILES")
        print("-" * 60)
        for symbol, rows in too_short:
            print(f"{symbol}: {rows} rows")

    print("\nValidation complete.")