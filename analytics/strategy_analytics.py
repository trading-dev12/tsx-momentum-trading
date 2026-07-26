import csv
from pathlib import Path


class StrategyAnalytics:
    """
    Calculates performance statistics for an individual strategy.
    """

    def __init__(self, strategy_name, journal_path):
        self.strategy_name = strategy_name
        self.journal_path = Path(journal_path)

    def load_trades(self):
        """Load all trades from the journal."""
        if not self.journal_path.exists():
            return []

        with self.journal_path.open(
            mode="r",
            newline="",
            encoding="utf-8-sig",
        ) as journal_file:
            return list(csv.DictReader(journal_file))

    def total_trades(self):
        return len(self.load_trades())

    def winning_trades(self):
        return sum(
            1
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) > 0
        )

    def losing_trades(self):
        return sum(
            1
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) < 0
        )

    def win_rate(self):
        total = self.total_trades()
        if total == 0:
            return 0.0
        return (self.winning_trades() / total) * 100.0

    def realized_pl(self):
        return sum(
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
        )

    def average_win(self):
        wins = [
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) > 0
        ]

        if not wins:
            return 0.0

        return sum(wins) / len(wins)

    def average_loss(self):
        losses = [
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) < 0
        ]

        if not losses:
            return 0.0

        return sum(losses) / len(losses)

    def largest_win(self):
        wins = [
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) > 0
        ]

        return max(wins) if wins else 0.0

    def largest_loss(self):
        losses = [
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) < 0
        ]

        return min(losses) if losses else 0.0

    def profit_factor(self):
        gross_profit = sum(
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) > 0
        )

        gross_loss = abs(sum(
            float(trade.get("profit_loss", 0) or 0)
            for trade in self.load_trades()
            if float(trade.get("profit_loss", 0) or 0) < 0
        ))

        if gross_loss == 0:
            return 0.0

        return gross_profit / gross_loss

    def expectancy(self):
        if self.total_trades() == 0:
            return 0.0

        return self.realized_pl() / self.total_trades()

    def summary(self):
        return {
            "strategy": self.strategy_name,
            "total_trades": self.total_trades(),
            "winning_trades": self.winning_trades(),
            "losing_trades": self.losing_trades(),
            "win_rate": self.win_rate(),
            "realized_pl": self.realized_pl(),
            "average_win": self.average_win(),
            "average_loss": self.average_loss(),
            "largest_win": self.largest_win(),
            "largest_loss": self.largest_loss(),
            "profit_factor": self.profit_factor(),
            "expectancy": self.expectancy(),
        }