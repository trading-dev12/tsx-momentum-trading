"""
Final Strategy Validator

Compares a small set of strategy configurations to choose
the Version 3.0 paper-trading baseline.
"""

from research.universe_backtester import run_research_universe_backtest


strategies = []

for tmqs in [90, 95, 100]:
    for rvol in [1.5, 2.0, 2.5, 3.0]:
        strategies.append(
            {
                "name": f"T{tmqs}_R{rvol}",
                "tmqs": tmqs,
                "rvol": rvol,
                "breakout_only": True,
            }
        )


def score_result(summary):
    trades = summary.get("total_trades", 0)
    profit_factor = summary.get("profit_factor", 0)
    expectancy = summary.get("expectancy", 0)
    drawdown = abs(summary.get("max_drawdown", 0))

    if trades < 50:
        sample_penalty = 25
    elif trades < 100:
        sample_penalty = 10
    else:
        sample_penalty = 0

    score = (
        profit_factor * 25
        + expectancy * 10
        - drawdown * 5
        - sample_penalty
    )

    return round(score, 2)


def run_strategy_validation():
    print("\n" + "=" * 70)
    print("VERSION 3.0 FINAL STRATEGY VALIDATION")
    print("=" * 70)

    results = []

    for test in strategies:
        print("\n" + "-" * 70)
        print(f"Running Test: {test['name']}")
        print("-" * 70)

        trades, summary = run_research_universe_backtest(
            min_tmqs=test["tmqs"],
            min_rvol=test["rvol"],
            breakout_only=test["breakout_only"],
            return_summary=True,
            quiet=True,
        )

        score = score_result(summary)

        results.append({
            "name": test["name"],
            "min_tmqs": test["tmqs"],
            "min_rvol": test["rvol"],
            "trades": summary.get("total_trades", 0),
            "win_rate": summary.get("win_rate", 0),
            "profit_factor": summary.get("profit_factor", 0),
            "expectancy": summary.get("expectancy", 0),
            "max_drawdown": summary.get("max_drawdown", 0),
            "score": score,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "=" * 90)
    print("VALIDATION RESULTS")
    print("=" * 90)

    print(
        f"{'Name':<14}"
        f"{'TMQS':>8}"
        f"{'RVOL':>8}"
        f"{'Trades':>10}"
        f"{'Win %':>10}"
        f"{'PF':>10}"
        f"{'Exp %':>10}"
        f"{'DD %':>10}"
        f"{'Score':>10}"
    )

    print("-" * 90)

    for r in results:
        print(
            f"{r['name']:<14}"
            f"{r['min_tmqs']:>8}"
            f"{r['min_rvol']:>8.1f}"
            f"{r['trades']:>10}"
            f"{r['win_rate']:>10.2f}"
            f"{r['profit_factor']:>10.2f}"
            f"{r['expectancy']:>10.2f}"
            f"{r['max_drawdown']:>10.2f}"
            f"{r['score']:>10.2f}"
        )

    winner = results[0]

    print("\n" + "=" * 70)
    print("RECOMMENDED VERSION 3.0 PAPER TRADING SETTINGS")
    print("=" * 70)

    print(f"Strategy:      {winner['name']}")
    print(f"Minimum TMQS:  {winner['min_tmqs']}")
    print(f"Minimum RVOL:  {winner['min_rvol']}")
    print("Breakout Only: True")
    print(f"Trades:        {winner['trades']}")
    print(f"Win Rate:      {winner['win_rate']:.2f}%")
    print(f"Profit Factor: {winner['profit_factor']:.2f}")
    print(f"Expectancy:    {winner['expectancy']:.2f}%")
    print(f"Max Drawdown:  {winner['max_drawdown']:.2f}%")
    print(f"Score:         {winner['score']:.2f}")

    print("\n✓ Recommended for paper trading validation.")

    return winner


if __name__ == "__main__":
    run_strategy_validation()