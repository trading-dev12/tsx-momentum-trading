import pandas as pd

from research.oversold_context import (
    calculate_oversold_context,
    classify_recovery_state,
)


def make_history(
    closes,
    volume=100000,
):
    dates = pd.bdate_range(
        "2025-01-01",
        periods=len(closes),
    )

    close = pd.Series(
        closes,
        index=dates,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "Open": close * 1.001,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": float(volume),
        },
        index=dates,
    )


def test_deep_selloff_is_identified_as_oversold():
    rising = [
        100.0
        + (
            index * 0.10
        )
        for index in range(290)
    ]

    selloff = [
        129.0
        - (
            index * 1.6
        )
        for index in range(30)
    ]

    history = make_history(
        rising + selloff
    )

    def provider(
        symbol,
        measurement_date,
    ):
        return (
            history,
            "TEST_DATA",
        )

    result = (
        calculate_oversold_context(
            "TEST.TO",
            measurement_date=(
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
            history_provider=(
                provider
            ),
        )
    )

    assert (
        result["status"]
        == "AVAILABLE"
    )

    assert (
        result["rsi_14"]
        < 30
    )

    assert (
        result["rsi_state"]
        in {
            "OVERSOLD",
            "EXTREMELY_OVERSOLD",
        }
    )

    assert (
        result[
            "overall_context"
        ]
        in {
            "OVERSOLD",
            "DEEPLY_OVERSOLD",
        }
    )

    assert (
        result["research_only"]
        is True
    )


def test_52_week_location_is_calculated():
    closes = [
        75.0
        + (
            index * 0.20
        )
        for index in range(320)
    ]

    history = make_history(
        closes
    )

    def provider(
        symbol,
        measurement_date,
    ):
        return (
            history,
            "TEST_DATA",
        )

    result = (
        calculate_oversold_context(
            "ABC.TO",
            measurement_date=(
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
            history_provider=(
                provider
            ),
        )
    )

    assert (
        result["status"]
        == "AVAILABLE"
    )

    assert (
        result["week_52_high"]
        > result["week_52_low"]
    )

    assert (
        0
        <= result[
            "week_52_position_percent"
        ]
        <= 100
    )

    assert (
        result[
            "drawdown_from_52week_high_percent"
        ]
        >= 0
    )


def test_recovery_state_distinguishes_recovery():
    state = (
        classify_recovery_state(
            overall_context="NORMAL",
            current_close=101.0,
            previous_close=99.0,
            current_rsi=32.0,
            previous_rsi=28.0,
            recent_rsi_min=24.0,
        )
    )

    assert (
        state
        == "RECOVERING_FROM_OVERSOLD"
    )


def test_insufficient_history_is_unavailable():
    history = make_history(
        [
            100.0
            + index
            for index
            in range(100)
        ]
    )

    def provider(
        symbol,
        measurement_date,
    ):
        return (
            history,
            "TEST_DATA",
        )

    result = (
        calculate_oversold_context(
            "SHORT.TO",
            measurement_date=(
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
            history_provider=(
                provider
            ),
        )
    )

    assert (
        result["status"]
        == "UNAVAILABLE"
    )

    assert (
        "252"
        in result["reason"]
    )


def test_strong_upward_extension_is_not_called_normal():
    base = [
        100.0
        + (
            index * 0.05
        )
        for index in range(290)
    ]

    surge = [
        114.5
        + (
            index * 1.6
        )
        for index in range(30)
    ]

    history = make_history(
        base + surge
    )

    def provider(
        symbol,
        measurement_date,
    ):
        return (
            history,
            "TEST_DATA",
        )

    result = (
        calculate_oversold_context(
            "HOT.TO",
            measurement_date=(
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
            history_provider=(
                provider
            ),
        )
    )

    assert (
        result["status"]
        == "AVAILABLE"
    )

    assert (
        result[
            "extension_signal_count"
        ]
        >= 2
    )

    assert (
        result["overall_context"]
        in {
            "EXTENDED",
            "OVERBOUGHT",
        }
    )

    assert (
        result["overall_context"]
        != "NORMAL"
    )


def test_atr_extension_is_classified():
    from research.oversold_context import (
        classify_atr_pullback,
    )

    assert (
        classify_atr_pullback(2.25)
        == "DEEPLY_EXTENDED"
    )

    assert (
        classify_atr_pullback(1.60)
        == "EXTENDED_ABOVE_SMA20"
    )

    assert (
        classify_atr_pullback(-2.10)
        == "DEEP_PULLBACK"
    )
