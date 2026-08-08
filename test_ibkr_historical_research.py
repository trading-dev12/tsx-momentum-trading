from dataclasses import dataclass

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


@dataclass
class FakeBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class FakeProvider:
    def __init__(self):
        self.calls = []

    def get_historical_bars(
        self,
        symbol,
        duration,
        bar_size,
        use_rth,
        what_to_show,
    ):
        self.calls.append(
            {
                "symbol": symbol,
                "duration": duration,
                "bar_size": bar_size,
                "use_rth": use_rth,
                "what_to_show": (
                    what_to_show
                ),
            }
        )

        return [
            FakeBar(
                "2026-08-06",
                170.0,
                173.0,
                169.0,
                172.0,
                1000000,
            ),
            FakeBar(
                "2026-08-07",
                172.0,
                177.0,
                171.0,
                176.5,
                800000,
            ),
            FakeBar(
                "2026-08-08",
                176.5,
                178.0,
                175.0,
                177.0,
                700000,
            ),
        ]


def test_ibkr_research_history_uses_adjusted_data():
    provider = FakeProvider()

    frame = load_ibkr_daily_history(
        symbol="CNR.TO",
        measurement_date="2026-08-07",
        provider=provider,
    )

    assert len(frame) == 2

    assert (
        frame.iloc[-1]["close"]
        == 176.5
    )

    assert (
        provider.calls[0][
            "what_to_show"
        ]
        == "ADJUSTED_LAST"
    )

    assert (
        frame.attrs["data_source"]
        == "IBKR"
    )

    assert (
        frame.attrs[
            "historical_data_type"
        ]
        == "ADJUSTED_LAST"
    )


def test_ibkr_research_history_can_use_trades():
    provider = FakeProvider()

    frame = load_ibkr_daily_history(
        symbol="CNR.TO",
        adjusted=False,
        provider=provider,
    )

    assert len(frame) == 3

    assert (
        provider.calls[0][
            "what_to_show"
        ]
        == "TRADES"
    )

    assert (
        frame.attrs[
            "historical_data_type"
        ]
        == "TRADES"
    )
