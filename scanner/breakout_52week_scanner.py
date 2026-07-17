"""Shadow scanner for the 52-week breakout strategy."""

import csv
import os
from datetime import datetime

from core.watchlist_loader import load_all_watchlists
from core.market_data import get_live_quote
from strategies.breakout_52week_adapter import build_breakout_52week_input
from strategies.breakout_52week_strategy import (
    Breakout52WeekStrategy,
    Decision,
)


def scan_52_week_breakouts(watchlist):
    """
    Evaluate every symbol using the 52-week breakout strategy.

    This is shadow research only:
    - no paper trades
    - no pending queue
    - no portfolio changes
    """

    strategy = Breakout52WeekStrategy()

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

            strategy_input = build_breakout_52week_input(quote)
            strategy_result = strategy.evaluate(strategy_input)

            record = {
                "symbol": symbol,
                "strategy": "52_WEEK_BREAKOUT",
                "decision": strategy_result.decision.value,
                "reason": strategy_result.reason,
                "price": quote.get("price", 0),
                "prior_52_week_high": quote.get(
                    "prior_52_week_high",
                    0,
                ),
                "average_volume": quote.get(
                    "average_volume",
                    0,
                ),
                "rvol": quote.get("relative_volume", 0),
                "sma_50": quote.get("sma_50", 0),
                "sma_200": quote.get("sma_200", 0),
                "breakout": strategy_result.breakout,
            }

            if strategy_result.decision == Decision.READY:
                results["ready"].append(record)
            elif strategy_result.decision == Decision.WATCH:
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
    folder = "research/52_week_results"
    os.makedirs(folder, exist_ok=True)

    rows = (
        results["ready"]
        + results["watch"]
        + results["ignore"]
    )

    if not rows:
        print("\nNo 52-week results to save.")
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
        "prior_52_week_high",
        "average_volume",
        "rvol",
        "sma_50",
        "sma_200",
        "breakout",
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

    results = scan_52_week_breakouts(watchlist)

    save_results(results)

    print()
    print("=" * 70)
    print("52-WEEK BREAKOUT SHADOW SCAN")
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
                f" RVOL {trade['rvol']:.2f}"
                f"  High {trade['prior_52_week_high']:.2f}"
            )

    if results["watch"]:
        print("\nWATCH SYMBOLS")
        print("-" * 70)

        for trade in results["watch"]:
            print(
                f"{trade['symbol']:8}"
                f" RVOL {trade['rvol']:.2f}"
                f"  Price {trade['price']:.2f}"
                f"  High {trade['prior_52_week_high']:.2f}"
                f"  Reason: {trade['reason']}"
            )