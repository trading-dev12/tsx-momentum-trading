"""
Backtesting engine for TSX Momentum Trading system.
"""

import os

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance
from backtesting.reports import print_performance_report, save_trade_log



def run_backtest(
    file_path,
    min_tmqs=80,
    min_rvol=1.0,
    breakout_only=True,
    atr_multiplier=2.0,
    reward_multiplier=2.5,
    max_hold_days=10,
):
    rows = load_historical_csv(file_path)
    trades = []

    for index in range(1, len(rows)):
        row = rows[index]
        previous_row = rows[index - 1]

        signal = evaluate_historical_setup(row, previous_row)

        if signal["tmqs"] < min_tmqs:
            continue

        if signal["rvol"] < min_rvol:
            continue

        if breakout_only and signal.get("breakout", "") not in [
            "BREAKOUT",
            "STRONG BREAKOUT",
        ]:
            continue
        if signal["decision"] == "READY":
            print(
                f"READY RVOL CHECK | "
                f"TMQS={signal['tmqs']} | "
                f"RVOL={signal['rvol']:.2f} | "
                f"Breakout={signal['breakout']}"
        )
        if signal["decision"] == "READY":
            trade = simulate_trade(
                rows,
                index,
                atr_multiplier=atr_multiplier,
                reward_multiplier=reward_multiplier,
                max_hold_days=max_hold_days,
            )

            if trade is None:
                continue

            trade["reason"] = signal["reason"]
            trade["tmqs"] = signal["tmqs"]
            trade["rvol"] = signal["rvol"]
            trade["breakout"] = signal["breakout"]

            trades.append(trade)

    return trades


def run_watchlist_backtest(
    historical_folder="data/historical",
    min_tmqs=80,
    min_rvol=1.0,
    breakout_only=True,
    atr_multiplier=2.0,
    reward_multiplier=2.5,
    max_hold_days=10,
    show_report=True,
    save_log=True,
    verbose=True,
):
    all_trades = []

    files = [
        file
        for file in os.listdir(historical_folder)
        if file.endswith(".csv")
    ]

    if verbose:
        print(f"Found {len(files)} historical files.\n")

    for file in files:
        file_path = os.path.join(historical_folder, file)

        symbol = file.replace("_TO.csv", ".TO").replace(".csv", "")

        if verbose:
            print(f"Backtesting {symbol}...")

        trades = run_backtest(
            file_path,
            min_tmqs=min_tmqs,
            min_rvol=min_rvol,
            breakout_only=breakout_only,
            atr_multiplier=atr_multiplier,
            reward_multiplier=reward_multiplier,
            max_hold_days=max_hold_days,
        )

        for trade in trades:
            trade["symbol"] = symbol

        if verbose:
            print(f"Trades: {len(trades)}\n")

        all_trades.extend(trades)

    stats = calculate_performance(all_trades)

    if show_report:
        print_performance_report(stats)

    if save_log:
        save_trade_log(all_trades)

    return {
        "trades": all_trades,
        "summary": stats,
    }


if __name__ == "__main__":
    run_watchlist_backtest()