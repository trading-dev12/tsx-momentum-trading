"""
Main backtesting engine for the TSX Momentum Trading system.
"""

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance
from backtesting.reports import print_performance_report


def run_backtest(file_path):
    rows = load_historical_csv(file_path)

    trades = []

    for index in range(1, len(rows)):
        row = rows[index]
        previous_row = rows[index - 1]

        signal = evaluate_historical_setup(row, previous_row)

        if signal["decision"] == "READY":
            trade = simulate_trade(rows, index)
            trade["symbol"] = file_path
            trade["reason"] = signal["reason"]
            trades.append(trade)

    stats = calculate_performance(trades)
    print_performance_report(stats)

    return trades, stats


if __name__ == "__main__":
    run_backtest("data/historical/RY_TO.csv")