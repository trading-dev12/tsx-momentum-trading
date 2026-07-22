"""
Shadow scanner for the Mean Reversion research strategy.

This scanner never places trades and never interacts with the
paper portfolio or pending trade queue.
"""

import csv
import os
from dataclasses import dataclass
from datetime import datetime

from core.market_data import get_live_quote
from core.watchlist_loader import load_all_watchlists
from strategies.mean_reversion_adapter import (
    build_mean_reversion_input,
)
from strategies.mean_reversion_strategy import (
    MeanReversionInput,
    MeanReversionStrategy,
)


@dataclass
class ScanResult:
    symbol: str
    decision: str
    reason: str


class MeanReversionScanner:
    """Research-only scanner for mean reversion opportunities."""

    def __init__(self):
        self.strategy = MeanReversionStrategy()

    def evaluate_stock(
        self,
        symbol: str,
        indicator_data: MeanReversionInput,
    ) -> ScanResult:
        """Evaluate one stock using the Mean Reversion strategy."""

        result = self.strategy.evaluate(indicator_data)

        return ScanResult(
            symbol=symbol,
            decision=result.decision.value,
            reason=result.reason,
        )


def scan_mean_reversion(watchlist):
    """
    Evaluate every symbol using the Mean Reversion strategy.

    This is shadow research only:
    - no paper trades
    - no pending queue
    - no portfolio changes
    """

    scanner = MeanReversionScanner()

    results = {
        "ready": [],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    for symbol in watchlist:
        try:
            quote = get_live_quote(symbol)

            if quote is None:
                results["errors"].append(
                    {
                        "symbol": symbol,
                        "reason": "Market data unavailable",
                    }
                )
                continue

            strategy_input = build_mean_reversion_input(quote)

            scan_result = scanner.evaluate_stock(
                symbol,
                strategy_input,
            )

            price = float(quote.get("price", 0) or 0)
            sma_20 = float(quote.get("sma_20", 0) or 0)
            lower_band = float(
                quote.get("bollinger_lower", 0) or 0
            )

            price_vs_sma20_percent = (
                ((price / sma_20) - 1) * 100
                if sma_20 > 0
                else 0.0
            )

            price_vs_lower_band_percent = (
                ((price / lower_band) - 1) * 100
                if lower_band > 0
                else 0.0
            )

            record = {
                "symbol": symbol,
                "strategy": "MEAN_REVERSION",
                "decision": scan_result.decision,
                "reason": scan_result.reason,
                "price": price,
                "sma_20": sma_20,
                "rsi_2": quote.get("rsi_2", 0),
                "rsi_14": quote.get("rsi_14", 0),
                "bollinger_lower": lower_band,
                "price_vs_sma20_percent": round(
                    price_vs_sma20_percent,
                    4,
                ),
                "price_vs_lower_band_percent": round(
                    price_vs_lower_band_percent,
                    4,
                ),
            }

            if scan_result.decision == "READY":
                results["ready"].append(record)
            elif scan_result.decision == "WATCH":
                results["watch"].append(record)
            else:
                results["ignore"].append(record)

        except Exception as error:
            results["errors"].append(
                {
                    "symbol": symbol,
                    "reason": str(error),
                }
            )

    return results


def save_results(results):
    """Save the daily Mean Reversion research scan to CSV."""

    folder = "research/mean_reversion_results"
    os.makedirs(folder, exist_ok=True)

    rows = (
        results["ready"]
        + results["watch"]
        + results["ignore"]
    )

    if not rows:
        print("\nNo Mean Reversion results to save.")
        return None

    filename = os.path.join(
        folder,
        datetime.now().strftime("%Y-%m-%d") + ".csv",
    )

    fieldnames = [
        "symbol",
        "strategy",
        "decision",
        "reason",
        "price",
        "sma_20",
        "rsi_2",
        "rsi_14",
        "bollinger_lower",
        "price_vs_sma20_percent",
        "price_vs_lower_band_percent",
    ]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved results to {filename}")

    return filename


if __name__ == "__main__":
    watchlist = load_all_watchlists()

    results = scan_mean_reversion(watchlist)

    save_results(results)

    print()
    print("=" * 70)
    print("MEAN REVERSION SHADOW SCAN")
    print("=" * 70)

    print(f"READY : {len(results['ready'])}")
    print(f"WATCH : {len(results['watch'])}")
    print(f"IGNORE: {len(results['ignore'])}")
    print(f"ERRORS: {len(results['errors'])}")

    if results["ready"]:
        print("\nREADY SYMBOLS")
        print("-" * 70)

        for trade in results["ready"]:
            print(
                f"{trade['symbol']:8}"
                f" RSI2 {trade['rsi_2']:.2f}"
                f"  Price {trade['price']:.2f}"
                f"  Lower Band {trade['bollinger_lower']:.2f}"
            )

    if results["watch"]:
        print("\nWATCH SYMBOLS")
        print("-" * 70)

        for trade in results["watch"]:
            print(
                f"{trade['symbol']:8}"
                f" RSI2 {trade['rsi_2']:.2f}"
                f"  Price {trade['price']:.2f}"
                f"  SMA20 {trade['sma_20']:.2f}"
                f"  Reason: {trade['reason']}"
            )

    if results["errors"]:
        print("\nERRORS")
        print("-" * 70)

        for error in results["errors"]:
            print(
                f"{error['symbol']:8}"
                f" {error['reason']}"
            )
