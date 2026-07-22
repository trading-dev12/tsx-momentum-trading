"""
Mean Reversion Strategy

Research-only strategy.

This strategy evaluates whether a stock appears temporarily oversold
and may be a candidate for a mean reversion bounce.

It NEVER places trades.
It ONLY returns a research decision.
"""

from dataclasses import dataclass
from enum import Enum


class MeanReversionDecision(Enum):
    READY = "READY"
    WATCH = "WATCH"
    IGNORE = "IGNORE"


@dataclass
class MeanReversionInput:
    close: float
    sma20: float
    rsi2: float
    rsi14: float
    lower_band: float


@dataclass
class MeanReversionResult:
    decision: MeanReversionDecision
    reason: str


class MeanReversionStrategy:
    """
    Research-only mean reversion strategy.
    """

    RSI2_READY = 10
    RSI2_WATCH = 20

    def evaluate(
        self,
        data: MeanReversionInput,
    ) -> MeanReversionResult:

        if data.close < data.lower_band and data.rsi2 <= self.RSI2_READY:
            return MeanReversionResult(
                MeanReversionDecision.READY,
                "Below lower Bollinger Band with extremely oversold RSI2.",
            )

        if data.rsi2 <= self.RSI2_WATCH:
            return MeanReversionResult(
                MeanReversionDecision.WATCH,
                "RSI2 indicates possible oversold condition.",
            )

        return MeanReversionResult(
            MeanReversionDecision.IGNORE,
            "No mean reversion setup.",
        )