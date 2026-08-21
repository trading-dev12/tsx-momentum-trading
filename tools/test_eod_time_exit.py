from types import SimpleNamespace

from paper_trading.eod_time_exit import (
    run_eod_time_exits,
)


class Bar:
    def __init__(
        self,
        date,
        close,
    ):
        self.date = date
        self.close = close


class FakeProvider:
    def __init__(
        self,
        bars,
    ):
        self.bars = bars

    def get_historical_bars(
        self,
        **kwargs,
    ):
        return self.bars


class FakeEngine:
    def __init__(
        self,
        positions,
    ):
        self.portfolio = SimpleNamespace(
            open_positions=positions
        )

        self.closed = []

    def refresh_runtime_state(self):
        pass

    def close_position(
        self,
        **kwargs,
    ):
        self.closed.append(kwargs)

        symbol = kwargs["symbol"]

        self.portfolio.open_positions = [
            position
            for position
            in self.portfolio.open_positions
            if position["symbol"] != symbol
        ]

        return {
            "success": True,
            "trade": {
                "symbol": symbol,
            },
        }


def position(
    entry_date,
):
    return {
        "symbol": "TEST.TO",
        "entry_date": entry_date,
        "entry_price": 100.0,
        "stop_price": 90.0,
        "target_price": 110.0,
        "max_hold_days": 10,
    }


def test_exact_day10_closes_at_daily_close():
    engine = FakeEngine(
        [
            position(
                "2026-08-10"
            )
        ]
    )

    provider = FakeProvider(
        [
            Bar(
                "2026-08-21",
                103.67,
            )
        ]
    )

    result = run_eod_time_exits(
        engines={
            "mean_reversion": engine
        },
        current_date="2026-08-21",
        provider=provider,
    )

    assert result["success"] is True
    assert result["due"] == 1
    assert result["closed"] == 1

    close = engine.closed[0]

    assert close["exit_price"] == 103.67
    assert (
        close["exit_reason"]
        == "Time exit"
    )

    assert (
        close["current_datetime"]
        .strftime("%H:%M")
        == "16:00"
    )


def test_day9_is_left_open():
    engine = FakeEngine(
        [
            position(
                "2026-08-11"
            )
        ]
    )

    provider = FakeProvider([])

    result = run_eod_time_exits(
        engines={
            "mean_reversion": engine
        },
        current_date="2026-08-21",
        provider=provider,
    )

    assert result["success"] is True
    assert result["due"] == 0
    assert result["closed"] == 0
    assert len(
        engine.portfolio.open_positions
    ) == 1


def test_missing_close_fails_safely():
    engine = FakeEngine(
        [
            position(
                "2026-08-10"
            )
        ]
    )

    provider = FakeProvider([])

    result = run_eod_time_exits(
        engines={
            "mean_reversion": engine
        },
        current_date="2026-08-21",
        provider=provider,
    )

    assert result["success"] is False
    assert result["due"] == 1
    assert result["closed"] == 0
    assert len(result["errors"]) == 1

    # The position must remain open if
    # the official close cannot be obtained.
    assert len(
        engine.portfolio.open_positions
    ) == 1
