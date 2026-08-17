from datetime import datetime
from types import SimpleNamespace

from core.market_hours import TORONTO_TIMEZONE
from paper_trading import morning_recorder


class FakeProvider:
    def __init__(self, bars):
        self.bars = bars
        self.disconnected = False

    def get_historical_bars(
        self,
        symbol,
        duration,
        bar_size,
        use_rth,
        what_to_show,
    ):
        assert symbol == "TEST.TO"
        assert duration == "2 D"
        assert bar_size == "1 min"
        assert use_rth is True
        assert what_to_show == "TRADES"

        return self.bars

    def disconnect(self):
        self.disconnected = True


def make_bar(
    hour,
    minute,
    open_price,
    high,
    low,
    close,
    volume,
):
    return SimpleNamespace(
        date=datetime(
            2026,
            8,
            18,
            hour,
            minute,
            tzinfo=TORONTO_TIMEZONE,
        ),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_ibkr_minute_provider_returns_latest_bar_and_cumulative_volume():
    provider = FakeProvider(
        [
            make_bar(
                9,
                30,
                10.0,
                10.2,
                9.9,
                10.1,
                100,
            ),
            make_bar(
                9,
                31,
                10.1,
                10.3,
                10.0,
                10.2,
                150,
            ),
            make_bar(
                9,
                32,
                10.2,
                10.4,
                10.1,
                10.3,
                200,
            ),
        ]
    )

    result = (
        morning_recorder
        .get_latest_ibkr_one_minute_bar(
            "TEST.TO",
            current_datetime=datetime(
                2026,
                8,
                18,
                9,
                31,
                30,
                tzinfo=TORONTO_TIMEZONE,
            ),
            provider=provider,
        )
    )

    assert result["success"] is True
    assert result["close_price"] == 10.2
    assert result["volume"] == 150
    assert result["cumulative_volume"] == 250
    assert (
        result["data_source"]
        == "IBKR_ONE_MINUTE"
    )


def test_combined_provider_prefers_ibkr(
    monkeypatch,
):
    monkeypatch.setattr(
        morning_recorder,
        "get_latest_ibkr_one_minute_bar",
        lambda symbol, current_datetime=None: {
            "success": True,
            "symbol": symbol,
            "close_price": 10.2,
            "data_source": "IBKR_ONE_MINUTE",
        },
    )

    def yahoo_should_not_run(
        symbol,
        current_datetime=None,
    ):
        raise AssertionError(
            "Yahoo should not run when IBKR succeeds."
        )

    monkeypatch.setattr(
        morning_recorder,
        "get_latest_yahoo_one_minute_bar",
        yahoo_should_not_run,
    )

    result = (
        morning_recorder
        .get_latest_one_minute_bar(
            "TEST.TO"
        )
    )

    assert result["success"] is True
    assert (
        result["data_source"]
        == "IBKR_ONE_MINUTE"
    )


def test_combined_provider_uses_yahoo_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        morning_recorder,
        "get_latest_ibkr_one_minute_bar",
        lambda symbol, current_datetime=None: {
            "success": False,
            "symbol": symbol,
            "message": "TWS unavailable",
        },
    )

    monkeypatch.setattr(
        morning_recorder,
        "get_latest_yahoo_one_minute_bar",
        lambda symbol, current_datetime=None: {
            "success": True,
            "symbol": symbol,
            "close_price": 10.1,
            "data_source": "YAHOO_ONE_MINUTE",
        },
    )

    result = (
        morning_recorder
        .get_latest_one_minute_bar(
            "TEST.TO"
        )
    )

    assert result["success"] is True
    assert (
        result["data_source"]
        == "YAHOO_ONE_MINUTE_FALLBACK"
    )
    assert (
        result["primary_source_error"]
        == "TWS unavailable"
    )
