"""
Historical data loader for the TSX Momentum Trading backtester.
"""

from pathlib import Path
import csv


def load_historical_csv(file_path):
    """
    Load Yahoo Finance CSV data and return clean OHLCV rows.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Historical data file not found: {file_path}")

    rows = []

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        next(reader)
        next(reader)

        for row in reader:
            clean_row = {
                "date": row["Price"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "adj_close": float(row["Adj Close"]),
                "volume": int(float(row["Volume"])),
            }

            rows.append(clean_row)

    return rows


def test_load_ry():
    file_path = "data/historical/RY_TO.csv"
    rows = load_historical_csv(file_path)

    print(f"Loaded rows: {len(rows)}")
    print("First row:")
    print(rows[0])
    print("Last row:")
    print(rows[-1])


if __name__ == "__main__":
    test_load_ry()