"""
Main backtesting engine for the TSX Momentum Trading system.
"""

from backtesting.historical_loader import load_historical_csv, validate_historical_data
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance
from backtesting.reports import print_performance_report


def run_backtest(file_path):
    rows = load_historical_csv(file_path)

    is_valid, message = validate_historical_data(rows)

    if not is_valid:
        print(f"Backtest stopped: {message}")
        return

    trades = []

    for index in range(1, len(rows)):
        row = rows[index]
        previous_row = rows[index - 1]

        signal = evaluate_historical_setup(row, previous_row)

        if signal["decision"] == "READY":
            trade = simulate_trade(rows, index)
            trade["reason"] = signal["reason"]
            trades.append(trade)

    stats = calculate_performance(trades)
    print_performance_report(stats)

    return trades, stats