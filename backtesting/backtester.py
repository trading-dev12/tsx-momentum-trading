"""
Main backtesting engine for the TSX Momentum Trading system.
"""

from pathlib import Path

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance
from backtesting.reports import print_performance_report, save_trade_log


def run_backtest(file_path, min_tmqs=0, min_rvol=0, breakout_only=False):
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
            trade = simulate_trade(rows, index)

            if trade is None:
                continue

            trade["symbol"] = symbol
            trade["reason"] = signal["reason"]
            trades.append(trade)

    return trades


def run_watchlist_backtest(folder_path="data/historical"):
    folder = Path(folder_path)
    all_trades = []

    csv_files = sorted(folder.glob("*_TO.csv"))

    print(f"Found {len(csv_files)} historical files.\n")

    for file_path in csv_files:
        symbol = file_path.stem.replace("_TO", ".TO")
        print(f"Backtesting {symbol}...")

        trades = run_backtest(
            file_path,
            min_tmqs=95,
            min_rvol=2.0,
            breakout_only=True,
        )

        print(f"Trades: {len(trades)}\n")
        all_trades.extend(trades)

    stats = calculate_performance(all_trades)
    print_performance_report(stats)
    save_trade_log(all_trades)

    return all_trades, stats


if __name__ == "__main__":
    run_watchlist_backtest()