import csv
import glob
import os


WATCHLIST_FOLDER = "watchlists"


def clean_symbol(symbol):
    symbol = symbol.strip()

    if not symbol:
        return None

    if symbol.upper() == "SYMBOL":
        return None

    return symbol


def load_watchlist(filename):
    watchlist = []

    with open(filename, newline="") as file:
        reader = csv.reader(file)

        for row in reader:
            if not row:
                continue

            symbol = clean_symbol(row[0])

            if symbol:
                watchlist.append(symbol)

    return watchlist


def load_all_watchlists(folder=WATCHLIST_FOLDER):
    symbols = set()

    files = glob.glob(os.path.join(folder, "*.csv"))

    for file in files:
        for symbol in load_watchlist(file):
            symbols.add(symbol)

    return sorted(symbols)