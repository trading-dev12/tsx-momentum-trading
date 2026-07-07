"""
Yahoo Finance data provider for the TSX Momentum Trading project.
"""

from pathlib import Path
import yfinance as yf

from core.watchlist_loader import load_watchlist
from core.config_loader import load_settings


def download_history(symbol, period="5y", interval="1d"):
    print(f"Downloading {symbol}...")

    data = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        print(f"No data returned for {symbol}")
        return None

    output_folder = Path("data/historical")
    output_folder.mkdir(parents=True, exist_ok=True)

    output_file = output_folder / f"{symbol.replace('.', '_')}.csv"
    data.to_csv(output_file)

    print(f"Saved: {output_file}")
    return output_file


def download_watchlist(period="5y", interval="1d"):
    settings = load_settings()
    watchlist = load_watchlist(settings["watchlist_file"])

    print(f"Found {len(watchlist)} symbols in watchlist.\n")

    completed = 0
    failed = 0

    for symbol in watchlist:
        try:
            result = download_history(symbol, period=period, interval=interval)

            if result is None:
                failed += 1
            else:
                completed += 1

        except Exception as error:
            failed += 1
            print(f"FAILED: {symbol} - {error}")

    print("\n" + "=" * 50)
    print("YAHOO FINANCE DOWNLOAD COMPLETE")
    print("=" * 50)
    print(f"Completed: {completed}")
    print(f"Failed:    {failed}")
    print("=" * 50)


if __name__ == "__main__":
    download_watchlist()