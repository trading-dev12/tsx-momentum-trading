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
from research.market_snapshot import (
    build_market_snapshot,
)
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


def scan_mean_reversion(
    watchlist,
    measurement_date=None,
):
    """
    Evaluate every symbol using the Mean Reversion strategy.

    This is shadow research only:
    - no paper trades
    - no pending queue
    - no portfolio changes
    """

    scanner = MeanReversionScanner()

    signal_date = (
        measurement_date
        or datetime.now()
        .date()
        .isoformat()
    )

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

            sma_50 = float(
                quote.get("sma_50", 0)
                or 0
            )

            sma_200 = float(
                quote.get("sma_200", 0)
                or 0
            )

            volume = float(
                quote.get("volume", 0)
                or 0
            )

            atr = float(
                quote.get("atr", 0)
                or 0
            )

            grades = quote.get(
                "grades",
                {},
            ) or {}

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

            price_vs_sma50_percent = (
                (
                    (price - sma_50)
                    / sma_50
                )
                * 100
                if sma_50 > 0
                else 0.0
            )

            price_vs_sma200_percent = (
                (
                    (price - sma_200)
                    / sma_200
                )
                * 100
                if sma_200 > 0
                else 0.0
            )

            sma50_vs_sma200_percent = (
                (
                    (sma_50 - sma_200)
                    / sma_200
                )
                * 100
                if sma_200 > 0
                else 0.0
            )

            record = {
                "symbol": symbol,
                "strategy": "MEAN_REVERSION",
                "signal_date": signal_date,
                "close": price,
                "atr": atr,
                "tmqs": float(
                    quote.get("tmqs", 0) or 0
                ),
                "rvol": float(
                    quote.get(
                        "relative_volume",
                        0,
                    )
                    or 0
                ),
                "breakout": quote.get(
                    "breakout_status",
                    "NO_BREAKOUT",
                ),
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

                # Existing scanner context preserved for
                # post-validation research.
                "sma_50": sma_50,
                "sma_200": sma_200,
                "live_data_source": quote.get(
                    "data_source",
                    "",
                ),
                "price_source": quote.get(
                    "price_source",
                    "",
                ),
                "previous_close": quote.get(
                    "previous_close",
                    0,
                ),
                "previous_high": quote.get(
                    "previous_high",
                    0,
                ),
                "previous_low": quote.get(
                    "previous_low",
                    0,
                ),
                "gap_percent": quote.get(
                    "gap_percent",
                    0,
                ),
                "change_percent": quote.get(
                    "change_percent",
                    0,
                ),
                "volume": volume,
                "average_volume": quote.get(
                    "average_volume",
                    0,
                ),
                "dollar_volume": round(
                    price * volume,
                    2,
                ),
                "atr_percent": round(
                    (
                        atr
                        / price
                        * 100
                    )
                    if price > 0
                    else 0.0,
                    6,
                ),
                "score": quote.get(
                    "score",
                    0,
                ),
                "confidence_score": quote.get(
                    "confidence_score",
                    0,
                ),
                "rvol_status": quote.get(
                    "rvol_status",
                    "",
                ),
                "momentum_grade": grades.get(
                    "Momentum",
                    "",
                ),
                "liquidity_grade": grades.get(
                    "Liquidity",
                    "",
                ),
                "rvol_grade": grades.get(
                    "RVOL",
                    "",
                ),
                "breakout_status": quote.get(
                    "breakout_status",
                    "",
                ),
                "price_vs_sma50_percent": round(
                    price_vs_sma50_percent,
                    6,
                ),
                "price_vs_sma200_percent": round(
                    price_vs_sma200_percent,
                    6,
                ),
                "sma50_vs_sma200_percent": round(
                    sma50_vs_sma200_percent,
                    6,
                ),
            }

            record.update(
                build_market_snapshot(
                    "signal",
                    quote,
                    source=quote.get(
                        "data_source",
                        "",
                    ),
                )
            )

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


def save_results(
    results,
    measurement_date=None,
):
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

    if measurement_date is None:
        measurement_date = next(
            (
                str(
                    row.get(
                        "signal_date",
                        "",
                    )
                    or ""
                ).strip()
                for row in rows
                if str(
                    row.get(
                        "signal_date",
                        "",
                    )
                    or ""
                ).strip()
            ),
            "",
        )

    if not measurement_date:
        measurement_date = (
            datetime.now()
            .date()
            .isoformat()
        )

    filename = os.path.join(
        folder,
        f"{measurement_date}.csv",
    )

    fieldnames = [
        "symbol",
        "strategy",
        "signal_date",
        "decision",
        "reason",
        "close",
        "price",
        "atr",
        "tmqs",
        "rvol",
        "breakout",
        "sma_20",
        "rsi_2",
        "rsi_14",
        "bollinger_lower",
        "price_vs_sma20_percent",
        "price_vs_lower_band_percent",
        "sma_50",
        "sma_200",
        "live_data_source",
        "price_source",
        "previous_close",
        "previous_high",
        "previous_low",
        "gap_percent",
        "change_percent",
        "volume",
        "average_volume",
        "dollar_volume",
        "atr_percent",
        "score",
        "confidence_score",
        "rvol_status",
        "momentum_grade",
        "liquidity_grade",
        "rvol_grade",
        "breakout_status",
        "price_vs_sma50_percent",
        "price_vs_sma200_percent",
        "sma50_vs_sma200_percent",
        "signal_quote_status",
        "signal_quote_source",
        "signal_quote_timestamp",
        "signal_bid",
        "signal_ask",
        "signal_last",
        "signal_midpoint",
        "signal_spread_amount",
        "signal_spread_percent",
        "signal_quote_error",
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
            extrasaction="ignore",
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
