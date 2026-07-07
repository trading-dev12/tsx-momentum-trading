"""
Performance statistics for the TSX Momentum Trading backtester.
"""


def calculate_performance(trades):
    """
    Calculate basic backtest performance statistics.
    """

    if not trades:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "average_gain": 0,
            "average_loss": 0,
            "profit_factor": 0,
            "total_return_percent": 0,
        }

    winners = [trade for trade in trades if trade["profit_loss_percent"] > 0]
    losers = [trade for trade in trades if trade["profit_loss_percent"] <= 0]

    total_gain = sum(trade["profit_loss_percent"] for trade in winners)
    total_loss = sum(trade["profit_loss_percent"] for trade in losers)

    return {
        "total_trades": len(trades),
        "win_rate": (len(winners) / len(trades)) * 100,
        "average_gain": total_gain / len(winners) if winners else 0,
        "average_loss": total_loss / len(losers) if losers else 0,
        "profit_factor": abs(total_gain / total_loss) if total_loss != 0 else 0,
        "total_return_percent": sum(trade["profit_loss_percent"] for trade in trades),
    }