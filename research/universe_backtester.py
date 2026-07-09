"""
Research Universe Backtester

Runs the existing backtester across every historical CSV
in the research universe and combines the results.
"""
from research.stock_rankings import rank_stocks
import os
import glob
from backtesting.performance import calculate_performance
from backtesting.backtester import run_backtest


HISTORICAL_FOLDER = "data/historical"


def run_research_universe_backtest(
    min_tmqs=95,
    min_rvol=2.0,
    breakout_only=True,
):
    all_trades = []
    files = glob.glob(os.path.join(HISTORICAL_FOLDER, "*.csv"))

    print("=" * 60)
    print("TSX MOMENTUM RESEARCH UNIVERSE BACKTEST")
    print("=" * 60)

    print(f"Historical files found: {len(files)}")
    print(f"Minimum TMQS: {min_tmqs}")
    print(f"Minimum RVOL: {min_rvol}")
    print(f"Breakout only: {breakout_only}")
    print("-" * 60)

    for file_path in files:
        symbol = os.path.basename(file_path).replace("_TO.csv", ".TO")

        try:
        
            trades = run_backtest(
                file_path=file_path,
                min_tmqs=min_tmqs,
                min_rvol=min_rvol,
                breakout_only=breakout_only,
            )   

         

            for trade in trades:
                trade["symbol"] = symbol

            all_trades.extend(trades)

            print(f"{symbol:<10} Trades: {len(trades)}")

        except Exception as e:
            print(f"{symbol:<10} ERROR: {e}")

    print("-" * 60)
    print(f"Total trades collected: {len(all_trades)}")

    if all_trades:
        rank_stocks(all_trades)

        performance = calculate_performance(all_trades)

        print("\n" + "=" * 60)
        print("FULL UNIVERSE PERFORMANCE")
        print("=" * 60)

        for key, value in performance.items():
            print(f"{key}: {value}")

    print("\nUniverse backtest complete.")

    return all_trades