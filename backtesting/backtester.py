"""
Main backtesting engine for the TSX Momentum Trading system.
"""

from pathlib import Path

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance
from backtesting.reports import print_performance_report, save_trade_log


def run_backtest(
    file_path,
    min_tmqs=0,
    min_rvol=0,
    breakout_only=False,
    atr_multiplier=1.5,
    reward_multiplier=2.0,
    max_hold_days=7,
):
    rows = load_historical_csv(file_path)
    trades = []
    symbol = Path(file_path).stem.replace("_TO", ".TO")

    for index in range(1, len(rows)):
        row = rows[index]
        previous_row = rows[index - 1]

        signal = evaluate_historical_setup(row, previous_row)

        if signal.get("tmqs", 0) < min_tmqs:
            continue

        if signal.get("rvol", 0) < min_rvol:
            continue

        if breakout_only and signal.get("breakout", "") != "BREAKOUT":
            continue

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

            trade["symbol"] = symbol
            trade["reason"] = signal["reason"]
            trades.append(trade)

    return trades


def run_watchlist_backtest(
    folder_path="data/historical",
    min_tmqs=0,
    min_rvol=0,
    breakout_only=False,
    atr_multiplier=1.5,
    reward_multiplier=2.0,
    max_hold_days=7,
):
    folder = Path(folder_path)
    all_trades = []

    csv_files = sorted(folder.glob("*_TO.csv"))

    print(f"Found {len(csv_files)} historical files.\n")

    for file_path in csv_files:
        symbol = file_path.stem.replace("_TO", ".TO")
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

        print(f"Trades: {len(trades)}\n")
        all_trades.extend(trades)

    stats = calculate_performance(all_trades)
    print_performance_report(stats)
    save_trade_log(all_trades)

    return all_trades, stats


if __name__ == "__main__":
    run_watchlist_backtest()