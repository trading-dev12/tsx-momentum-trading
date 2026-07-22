"""
Out-of-Sample Validator
"""

import os
import glob

from backtesting.historical_loader import load_historical_csv
from backtesting.strategy import evaluate_historical_setup
from backtesting.trade_simulator import simulate_trade
from backtesting.performance import calculate_performance


HISTORICAL_FOLDER = "data/historical"


def run_out_of_sample_validation(
    split_year=2024,
    min_tmqs=100,
    min_rvol=1.5,
    breakout_only=True,
    slippage_percent=0.0,
):
    training_trades = []
    validation_trades = []

    files = glob.glob(os.path.join(HISTORICAL_FOLDER, "*.csv"))

    print("=" * 70)
    print("OUT-OF-SAMPLE VALIDATION")
    print("=" * 70)
    print(f"Historical files found: {len(files)}")
    print(f"Split year: {split_year}")
    print(f"Minimum TMQS: {min_tmqs}")
    print(f"Minimum RVOL: {min_rvol}")
    print(f"Breakout only: {breakout_only}")
    print(f"Slippage: {slippage_percent * 100:.2f}%")
    print("-" * 70)

    for file_path in files:
        symbol = os.path.basename(file_path).replace("_TO.csv", ".TO")

        try:
            rows = load_historical_csv(file_path)

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

                trade = simulate_trade(rows, index)

                if trade is None:
                    continue

                slippage_cost_percent = slippage_percent * 100 * 2

                trade["return_pct"] = trade["return_pct"] - slippage_cost_percent
                trade["profit_loss_percent"] = trade["return_pct"]

                trade["symbol"] = symbol
                trade["tmqs"] = signal["tmqs"]
                trade["rvol"] = signal["rvol"]
                trade["breakout"] = signal.get("breakout", "")
                trade["slippage_percent"] = slippage_percent

                trade_year = int(str(trade["entry_date"])[:4])

                if trade_year < split_year:
                    training_trades.append(trade)
                else:
                    validation_trades.append(trade)

        except Exception as e:
            print(f"{symbol:<10} ERROR: {e}")

    training_performance = calculate_performance(training_trades)
    validation_performance = calculate_performance(validation_trades)

    print("\nTRAINING PERIOD")
    print("-" * 70)
    print_performance(training_performance)

    print("\nVALIDATION PERIOD")
    print("-" * 70)
    print_performance(validation_performance)

    print("\nOUT-OF-SAMPLE SUMMARY")
    print("-" * 70)

    if (
        validation_performance["profit_factor"] >= 1.3
        and validation_performance["expectancy"] > 0
    ):
        print("PASS: Strategy remained profitable on unseen data.")
    else:
        print("FAIL: Strategy weakened on unseen data.")

    return {
        "training_trades": training_trades,
        "validation_trades": validation_trades,
        "training_performance": training_performance,
        "validation_performance": validation_performance,
    }


def print_performance(performance):
    print(f"Trades: {performance['total_trades']}")
    print(f"Win Rate: {performance['win_rate']:.2f}%")
    print(f"Profit Factor: {performance['profit_factor']:.2f}")
    print(f"Expectancy: {performance['expectancy']:.2f}%")
    print(f"Return: {performance['total_return']:.2f}%")
    print(f"Max Drawdown: {performance['max_drawdown']:.2f}%")