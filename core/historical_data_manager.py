"""
Historical Data Manager

Downloads and updates historical data
for every symbol in the research universe.
"""

import os
import glob

import yfinance as yf


WATCHLIST_FOLDER = "watchlists"
HISTORICAL_FOLDER = "data/historical"


def get_all_symbols():
    symbols = set()

    files = glob.glob(os.path.join(WATCHLIST_FOLDER, "*.csv"))

    for file in files:
        with open(file, "r") as f:
            for line in f:
                symbol = line.strip()

                if (
                    symbol
                    and not symbol.startswith("#")
                    and symbol.upper() != "SYMBOL"
                ):
                    symbols.add(symbol)

    return sorted(symbols)


def update_historical_database(period="5y"):

    symbols = get_all_symbols()

    print("=" * 60)
    print("UPDATING HISTORICAL DATABASE")
    print("=" * 60)

    for symbol in symbols:

        print(f"Downloading {symbol}...")

        try:

            data = yf.download(
                symbol,
                period=period,
                progress=False,
                auto_adjust=False,
            )

            if data.empty:
                print("  No data.")
                continue

            filename = symbol.replace(".", "_") + ".csv"

            path = os.path.join(
                HISTORICAL_FOLDER,
                filename,
            )

            data.to_csv(path)

            print("  Saved.")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nHistorical database updated.")