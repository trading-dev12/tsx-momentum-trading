"""
End-of-Day Signal Test

Evaluates yesterday's completed daily candle and reports
READY and WATCH setups for the next trading day.
"""

from datetime import datetime

import yfinance as yf

from backtesting.strategy import evaluate_historical_setup
from core.watchlist_loader import load_all_watchlists


def get_completed_daily_rows(symbol, period="10d"):
    yahoo_symbol = symbol if symbol.endswith(".TO") else f"{symbol}.TO"

    history = yf.Ticker(yahoo_symbol).history(
        period=period,
        interval="1d",
        auto_adjust=False,
    )

    if history is None or history.empty:
        return []

    rows = []
    today = datetime.now().date()

    for index, row in history.iterrows():
        row_date = index.date()

        # Ignore today's candle if the market is still open.
        if row_date >= today:
            continue

        rows.append(
            {
                "date": row_date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            }
        )

    return rows


def test_eod_signals():

    watchlist = load_all_watchlists()

    ready_signals = []
    watch_signals = []

    print("=" * 78)
    print("TSX MOMENTUM PRO - END OF DAY SIGNAL TEST")
    print("=" * 78)
    print()

    for symbol in watchlist:

        try:

            rows = get_completed_daily_rows(symbol)

            if len(rows) < 2:
                continue

            previous_row = rows[-2]
            signal_row = rows[-1]

            signal = evaluate_historical_setup(
                signal_row,
                previous_row,
            )

            result = {
                "symbol": symbol,
                "signal_date": signal_row["date"],
                "close": signal_row["close"],
                "tmqs": signal["tmqs"],
                "rvol": signal["rvol"],
                "breakout": signal["breakout"],
                "decision": signal["decision"],
                "reason": signal["reason"],

                "breakout_score": signal.get(
                    "breakout_score",
                    0,
                ),
                "volume_score": signal.get(
                    "volume_score",
                    0,
                ),
                "price_score": signal.get(
                    "price_score",
                    0,
                ),
            }

            if result["decision"] == "READY":
                ready_signals.append(result)

            elif result["decision"] == "WATCH":
                watch_signals.append(result)

        except Exception as error:
            print(f"{symbol}: {error}")

    ready_signals.sort(
        key=lambda x: (x["tmqs"], x["rvol"]),
        reverse=True,
    )

    watch_signals.sort(
        key=lambda x: (x["tmqs"], x["rvol"]),
        reverse=True,
    )

    print("=" * 78)
    print("READY FOR NEXT TRADING DAY")
    print("=" * 78)

    if not ready_signals:
        print("No READY setups.")
    else:

        for signal in ready_signals:

            print("=" * 70)
            print(f"{signal['symbol']}  TMQS {signal['tmqs']:.2f}")
            print(f"Signal Date     : {signal['signal_date']}")
            print(f"Close Price     : ${signal['close']:.2f}")
            print(f"RVOL            : {signal['rvol']:.2f}x")
            print(f"Breakout        : {signal['breakout']}")
            print()
            print(f"Breakout Score  : {signal['breakout_score']:.2f}/35")
            print(f"Volume Score    : {signal['volume_score']:.2f}/35")
            print(f"Price Score     : {signal['price_score']:.2f}/30")
            print()
            print(f"Decision        : {signal['decision']}")
            print(f"Reason          : {signal['reason']}")

    print()
    print("=" * 78)
    print("TOP WATCH SETUPS")
    print("=" * 78)

    if not watch_signals:
        print("No WATCH setups.")
    else:

        for signal in watch_signals[:10]:

            print("=" * 70)
            print(f"{signal['symbol']}  TMQS {signal['tmqs']:.2f}")
            print(f"Signal Date     : {signal['signal_date']}")
            print(f"Close Price     : ${signal['close']:.2f}")
            print(f"RVOL            : {signal['rvol']:.2f}x")
            print(f"Breakout        : {signal['breakout']}")
            print()
            print(f"Breakout Score  : {signal['breakout_score']:.2f}/35")
            print(f"Volume Score    : {signal['volume_score']:.2f}/35")
            print(f"Price Score     : {signal['price_score']:.2f}/30")
            print()
            print(f"Decision        : {signal['decision']}")
            print(f"Reason          : {signal['reason']}")


if __name__ == "__main__":
    test_eod_signals()