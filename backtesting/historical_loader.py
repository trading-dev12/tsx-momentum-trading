"""
Historical data loader for the TSX Momentum Trading backtester.

This module will eventually load real historical OHLCV data.
For now, it provides the clean structure we need for Version 2.0.
"""

from pathlib import Path
import csv


def load_historical_csv(file_path):
    """
    Load historical OHLCV data from a CSV file.

    Expected columns:
    date, open, high, low, close, volume

    Returns:
        list of dictionaries
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Historical data file not found: {file_path}")

    rows = []

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(
                {
                    "date": row["date"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(float(row["volume"])),
                }
            )

    return rows


def validate_historical_data(rows):
    """
    Basic validation for historical OHLCV data.
    """

    required_fields = ["date", "open", "high", "low", "close", "volume"]

    if not rows:
        return False, "No historical data loaded."

    for index, row in enumerate(rows):
        for field in required_fields:
            if field not in row:
                return False, f"Missing field '{field}' in row {index + 1}"

    return True, "Historical data is valid."