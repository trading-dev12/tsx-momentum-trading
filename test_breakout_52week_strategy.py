from strategies.breakout_52week_strategy import (
    Breakout52WeekStrategy,
    Breakout52WeekInput,
    Decision,
)


def make_input(**kwargs):
    data = {
        "symbol": "TEST.TO",
        "close": 100.0,
        "prior_52_week_high": 99.0,
        "average_volume": 500_000,
        "rvol": 2.0,
        "sma_50": 95.0,
        "sma_200": 90.0,
    }
    data.update(kwargs)
    return Breakout52WeekInput(**data)


def test_ready_breakout():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input())

    assert result.decision == Decision.READY
    assert result.breakout is True


def test_watch_breakout_low_rvol():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(rvol=1.2))

    assert result.decision == Decision.WATCH


def test_ignore_not_breakout():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(close=98.5))

    assert result.decision == Decision.IGNORE


def test_ignore_price():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(close=4.50))

    assert result.decision == Decision.IGNORE


def test_ignore_volume():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(average_volume=200000))

    assert result.decision == Decision.IGNORE


def test_ignore_trend():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(
        make_input(
            sma_50=80,
            sma_200=100,
        )
    )

    assert result.decision == Decision.IGNORE


def test_invalid_price():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(close=0))

    assert result.decision == Decision.IGNORE


def test_invalid_high():
    strategy = Breakout52WeekStrategy()
    result = strategy.evaluate(make_input(prior_52_week_high=0))

    assert result.decision == Decision.IGNORE
    assert result.reason == "Invalid 52-week high"