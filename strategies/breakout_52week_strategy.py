"""52-week breakout strategy.

This module is intentionally isolated from the existing momentum system.
It does not scan stocks, place trades, or modify the paper portfolio yet.
"""

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    READY = "READY"
    WATCH = "WATCH"
    IGNORE = "IGNORE"


@dataclass(frozen=True)
class Breakout52WeekConfig:
    minimum_price: float = 5.00
    minimum_average_volume: int = 300_000
    minimum_rvol: float = 1.50
    require_bullish_trend: bool = True


@dataclass(frozen=True)
class Breakout52WeekInput:
    symbol: str
    close: float
    prior_52_week_high: float
    average_volume: int
    rvol: float
    sma_50: float
    sma_200: float


@dataclass(frozen=True)
class Breakout52WeekResult:
    symbol: str
    decision: Decision
    reason: str
    breakout: bool


class Breakout52WeekStrategy:
    """Evaluates a stock against the initial 52-week breakout rules."""

    def __init__(self, config: Breakout52WeekConfig | None = None) -> None:
        self.config = config or Breakout52WeekConfig()

    def evaluate(self, data: Breakout52WeekInput) -> Breakout52WeekResult:
        if data.close <= 0:
            return self._result(data, Decision.IGNORE, "Invalid closing price")

        if data.prior_52_week_high <= 0:
            return self._result(data, Decision.IGNORE, "Invalid 52-week high")

        if data.close < self.config.minimum_price:
            return self._result(data, Decision.IGNORE, "Price below minimum")

        if data.average_volume < self.config.minimum_average_volume:
            return self._result(data, Decision.IGNORE, "Average volume too low")

        bullish_trend = data.sma_50 > data.sma_200

        if self.config.require_bullish_trend and not bullish_trend:
            return self._result(data, Decision.IGNORE, "50-day SMA is not above 200-day SMA")

        breakout = data.close >= data.prior_52_week_high

        if breakout and data.rvol >= self.config.minimum_rvol:
            return self._result(
                data,
                Decision.READY,
                "New 52-week high with confirmed relative volume",
                breakout=True,
            )

        if breakout:
            return self._result(
                data,
                Decision.WATCH,
                "52-week breakout but relative volume is too low",
                breakout=True,
            )

        return self._result(
            data,
            Decision.IGNORE,
            "Price has not reached the prior 52-week high",
        )

    @staticmethod
    def _result(
        data: Breakout52WeekInput,
        decision: Decision,
        reason: str,
        breakout: bool = False,
    ) -> Breakout52WeekResult:
        return Breakout52WeekResult(
            symbol=data.symbol,
            decision=decision,
            reason=reason,
            breakout=breakout,
        )