"""Shadow scanner for the 52-week breakout strategy."""

import csv
import os
from datetime import datetime

from core.watchlist_loader import load_all_watchlists
from core.market_data import get_live_quote
from research.market_snapshot import (
    build_market_snapshot,
)
from strategies.breakout_52week_adapter import build_breakout_52week_input
from strategies.breakout_52week_strategy import (
    Breakout52WeekStrategy,
    Decision,
)


def scan_52_week_breakouts(
    watchlist,
    signal_date=None,
):
    """
    Evaluate every symbol using the 52-week breakout strategy.

    This is shadow research only:
    - no paper trades
    - no pending queue
    - no portfolio changes
    """

    strategy = Breakout52WeekStrategy()

    if signal_date is None:
        signal_date = (
            datetime.now()
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

            strategy_input = build_breakout_52week_input(quote)
            strategy_result = strategy.evaluate(strategy_input)

            price = float(
                quote.get("price", 0)
                or 0
            )

            atr = float(
                quote.get("atr", 0)
                or 0
            )

            volume = float(
                quote.get("volume", 0)
                or 0
            )

            prior_high = float(
                quote.get(
                    "prior_52_week_high",
                    0,
                )
                or 0
            )

            sma_50 = float(
                quote.get("sma_50", 0)
                or 0
            )

            sma_200 = float(
                quote.get("sma_200", 0)
                or 0
            )

            grades = quote.get(
                "grades",
                {},
            ) or {}

            distance_to_high_percent = (
                (
                    (price - prior_high)
                    / prior_high
                )
                * 100
                if prior_high > 0
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
                "strategy": "52_WEEK_BREAKOUT",
                "decision": strategy_result.decision.value,
                "signal_date": signal_date,
                "close": price,
                "atr": atr,
                "tmqs": quote.get("tmqs", 0),
                "reason": strategy_result.reason,
                "price": price,
                "prior_52_week_high": prior_high,
                "average_volume": quote.get(
                    "average_volume",
                    0,
                ),
                "rvol": quote.get("relative_volume", 0),
                "sma_50": sma_50,
                "sma_200": sma_200,
                "breakout": strategy_result.breakout,

                # Existing scanner context preserved for
                # post-validation research.
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
                "distance_to_52_week_high_percent": round(
                    distance_to_high_percent,
                    6,
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


def save_results(
    results,
    signal_date=None,
):
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

    if signal_date is None:
        signal_date = next(
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

    if not signal_date:
        signal_date = (
            datetime.now()
            .date()
            .isoformat()
        )

    filename = os.path.join(
        folder,
        f"{signal_date}.csv",
    )

    fieldnames = [
        "symbol",
        "strategy",
        "decision",
        "reason",
        "price",
        "close",
        "atr",
        "tmqs",
        "signal_date",
        "prior_52_week_high",
        "average_volume",
        "rvol",
        "sma_50",
        "sma_200",
        "breakout",
        "live_data_source",
        "price_source",
        "previous_close",
        "previous_high",
        "previous_low",
        "gap_percent",
        "change_percent",
        "volume",
        "dollar_volume",
        "atr_percent",
        "score",
        "confidence_score",
        "rvol_status",
        "momentum_grade",
        "liquidity_grade",
        "rvol_grade",
        "breakout_status",
        "distance_to_52_week_high_percent",
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