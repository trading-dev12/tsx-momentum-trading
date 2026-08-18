"""
Northstar Quant
Oversold / Pullback Research Context

Read-only technical research for arbitrary TSX stocks.

This module identifies technical pullback and oversold
conditions. It does not produce a BUY signal and does not
modify any Northstar trading strategy or trading state.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


RSI_PERIOD = 14
STOCH_RSI_PERIOD = 14
MFI_PERIOD = 14
BOLLINGER_PERIOD = 20
BOLLINGER_STD_MULTIPLIER = 2.0
ATR_PERIOD = 14
WEEK_52_SESSIONS = 252
MINIMUM_HISTORY_ROWS = 252

OVERSOLD_IBKR_CLIENT_ID = 31


def normalize_history(history):
    """
    Normalize IBKR or Yahoo OHLCV history.
    """

    if (
        history is None
        or history.empty
    ):
        return pd.DataFrame()

    frame = history.copy()

    if isinstance(
        frame.columns,
        pd.MultiIndex,
    ):
        if "Close" in (
            frame.columns
            .get_level_values(0)
        ):
            frame = frame.droplevel(
                1,
                axis=1,
            )
        elif "Close" in (
            frame.columns
            .get_level_values(1)
        ):
            frame = frame.droplevel(
                0,
                axis=1,
            )

    rename_map = {
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }

    frame = frame.rename(
        columns=rename_map
    )

    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(
            frame["Date"],
            errors="coerce",
        )

        frame = frame.set_index(
            "Date"
        )

    frame.index = pd.to_datetime(
        frame.index,
        errors="coerce",
    )

    frame = frame[
        ~frame.index.isna()
    ]

    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    if not all(
        column in frame.columns
        for column in required
    ):
        return pd.DataFrame()

    frame = frame[
        required
    ].copy()

    for column in required:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
        ]
    )

    frame["Volume"] = (
        frame["Volume"]
        .fillna(0.0)
    )

    return (
        frame
        .sort_index()
        .drop_duplicates(
            keep="last"
        )
    )


def load_oversold_history(
    symbol,
    measurement_date,
):
    """
    Load one daily OHLCV dataset.

    IBKR TRADES is primary. Yahoo is fallback only.
    """

    ibkr_error = ""

    try:
        history = (
            load_ibkr_daily_history(
                symbol=symbol,
                measurement_date=(
                    measurement_date
                ),
                duration="2 Y",
                adjusted=False,
                client_id=(
                    OVERSOLD_IBKR_CLIENT_ID
                ),
            )
        )

        normalized = (
            normalize_history(
                history
            )
        )

        if (
            len(normalized)
            >= MINIMUM_HISTORY_ROWS
        ):
            return (
                normalized,
                "IBKR_TRADES",
            )

    except Exception as error:
        ibkr_error = str(
            error
        )

    measurement_datetime = (
        datetime.strptime(
            str(measurement_date),
            "%Y-%m-%d",
        )
    )

    start_date = (
        measurement_datetime
        - timedelta(days=650)
    )

    end_date = (
        measurement_datetime
        + timedelta(days=1)
    )

    try:
        history = yf.download(
            symbol,
            start=start_date.strftime(
                "%Y-%m-%d"
            ),
            end=end_date.strftime(
                "%Y-%m-%d"
            ),
            auto_adjust=False,
            progress=False,
            threads=False,
            multi_level_index=False,
        )

        normalized = (
            normalize_history(
                history
            )
        )

        if normalized.empty:
            raise ValueError(
                "Yahoo returned no usable history."
            )

        return (
            normalized,
            "YAHOO_FALLBACK",
        )

    except Exception as error:
        raise RuntimeError(
            "Oversold history unavailable. "
            f"IBKR: {ibkr_error or 'insufficient history'}; "
            f"Yahoo: {error}"
        ) from error


def calculate_rsi(
    close,
    period=RSI_PERIOD,
):
    """
    Calculate Wilder-style RSI.
    """

    delta = close.diff()

    gains = delta.clip(
        lower=0
    )

    losses = (
        -delta.clip(
            upper=0
        )
    )

    average_gain = gains.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    average_loss = losses.ewm(
        alpha=1.0 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    relative_strength = (
        average_gain
        / average_loss
    )

    rsi = (
        100.0
        - (
            100.0
            / (
                1.0
                + relative_strength
            )
        )
    )

    rsi = rsi.mask(
        (
            average_loss == 0
        )
        & (
            average_gain > 0
        ),
        100.0,
    )

    rsi = rsi.mask(
        (
            average_loss == 0
        )
        & (
            average_gain == 0
        ),
        50.0,
    )

    return rsi


def calculate_stoch_rsi(
    rsi,
    period=STOCH_RSI_PERIOD,
):
    """
    Calculate Stochastic RSI on a 0-100 scale.
    """

    rolling_min = (
        rsi.rolling(
            period
        ).min()
    )

    rolling_max = (
        rsi.rolling(
            period
        ).max()
    )

    denominator = (
        rolling_max
        - rolling_min
    )

    stoch = (
        (
            rsi
            - rolling_min
        )
        / denominator
        * 100.0
    )

    stoch = stoch.mask(
        denominator == 0,
        50.0,
    )

    return stoch


def calculate_mfi(
    history,
    period=MFI_PERIOD,
):
    """
    Calculate Money Flow Index.
    """

    typical_price = (
        history["High"]
        + history["Low"]
        + history["Close"]
    ) / 3.0

    raw_money_flow = (
        typical_price
        * history["Volume"]
    )

    direction = (
        typical_price.diff()
    )

    positive_flow = (
        raw_money_flow.where(
            direction > 0,
            0.0,
        )
    )

    negative_flow = (
        raw_money_flow.where(
            direction < 0,
            0.0,
        )
    )

    positive_sum = (
        positive_flow
        .rolling(period)
        .sum()
    )

    negative_sum = (
        negative_flow
        .rolling(period)
        .sum()
    )

    money_ratio = (
        positive_sum
        / negative_sum
    )

    mfi = (
        100.0
        - (
            100.0
            / (
                1.0
                + money_ratio
            )
        )
    )

    mfi = mfi.mask(
        (
            negative_sum == 0
        )
        & (
            positive_sum > 0
        ),
        100.0,
    )

    mfi = mfi.mask(
        (
            negative_sum == 0
        )
        & (
            positive_sum == 0
        ),
        50.0,
    )

    return mfi


def calculate_true_range(
    history,
):
    """
    Calculate daily True Range.
    """

    previous_close = (
        history["Close"]
        .shift(1)
    )

    return pd.concat(
        [
            (
                history["High"]
                - history["Low"]
            ),
            (
                history["High"]
                - previous_close
            ).abs(),
            (
                history["Low"]
                - previous_close
            ).abs(),
        ],
        axis=1,
    ).max(
        axis=1
    )


def classify_rsi(value):
    if value < 20:
        return "EXTREMELY_OVERSOLD"

    if value < 30:
        return "OVERSOLD"

    if value >= 70:
        return "OVERBOUGHT"

    return "NEUTRAL"


def classify_stoch_rsi(value):
    if value < 20:
        return "OVERSOLD"

    if value >= 80:
        return "OVERBOUGHT"

    return "NEUTRAL"


def classify_mfi(value):
    if value < 20:
        return "OVERSOLD"

    if value >= 80:
        return "OVERBOUGHT"

    return "NEUTRAL"


def classify_bollinger(
    percent_b,
):
    if percent_b < 0:
        return "BELOW_LOWER_BAND"

    if percent_b <= 0.10:
        return "NEAR_LOWER_BAND"

    if percent_b > 1.0:
        return "ABOVE_UPPER_BAND"

    return "INSIDE_BANDS"


def classify_atr_pullback(
    atr_distance,
):
    if atr_distance <= -2.0:
        return "DEEP_PULLBACK"

    if atr_distance <= -1.0:
        return "PULLBACK"

    if atr_distance >= 2.0:
        return "DEEPLY_EXTENDED"

    if atr_distance >= 1.5:
        return "EXTENDED_ABOVE_SMA20"

    return "NORMAL"


def classify_recovery_state(
    overall_context,
    current_close,
    previous_close,
    current_rsi,
    previous_rsi,
    recent_rsi_min,
):
    """
    Distinguish an ongoing decline from early recovery.
    """

    if (
        recent_rsi_min < 30
        and current_rsi >= 30
        and current_close > previous_close
    ):
        return (
            "RECOVERING_FROM_OVERSOLD"
        )

    if overall_context in {
        "OVERSOLD",
        "DEEPLY_OVERSOLD",
    }:
        if (
            current_close
            < previous_close
            and current_rsi
            <= previous_rsi
        ):
            return "STILL_FALLING"

        if (
            current_close
            > previous_close
            and current_rsi
            > previous_rsi
        ):
            return "STABILIZING"

        return (
            "RECOVERY_NOT_CONFIRMED"
        )

    if (
        overall_context
        == "PULLBACK"
    ):
        return (
            "PULLBACK_NOT_OVERSOLD"
        )

    return "NOT_OVERSOLD"


def calculate_oversold_context(
    symbol,
    measurement_date=None,
    history_provider=(
        load_oversold_history
    ),
):
    """
    Calculate Northstar's read-only pullback context.

    The final classification describes technical condition
    only. It is not a trading recommendation.
    """

    normalized_symbol = str(
        symbol or ""
    ).strip().upper()

    if not normalized_symbol:
        return {
            "status": "UNAVAILABLE",
            "reason": (
                "Symbol is required."
            ),
        }

    if measurement_date is None:
        measurement_date = (
            datetime.now()
            .strftime("%Y-%m-%d")
        )
    else:
        measurement_date = str(
            measurement_date
        ).strip()

    try:
        (
            history,
            data_source,
        ) = history_provider(
            normalized_symbol,
            measurement_date,
        )

        history = (
            normalize_history(
                history
            )
        )

        measurement_timestamp = (
            pd.Timestamp(
                measurement_date
            )
        )

        history = history[
            history.index.normalize()
            <= measurement_timestamp
        ]

        if (
            len(history)
            < MINIMUM_HISTORY_ROWS
        ):
            return {
                "symbol": (
                    normalized_symbol
                ),
                "measurement_date": (
                    measurement_date
                ),
                "status": (
                    "UNAVAILABLE"
                ),
                "reason": (
                    "At least "
                    f"{MINIMUM_HISTORY_ROWS} "
                    "daily sessions are required."
                ),
                "data_source": (
                    data_source
                ),
            }

        close = history["Close"]

        rsi = calculate_rsi(
            close
        )

        stoch_rsi = (
            calculate_stoch_rsi(
                rsi
            )
        )

        mfi = calculate_mfi(
            history
        )

        sma20 = (
            close
            .rolling(
                BOLLINGER_PERIOD
            )
            .mean()
        )

        std20 = (
            close
            .rolling(
                BOLLINGER_PERIOD
            )
            .std(
                ddof=0
            )
        )

        lower_band = (
            sma20
            - (
                BOLLINGER_STD_MULTIPLIER
                * std20
            )
        )

        upper_band = (
            sma20
            + (
                BOLLINGER_STD_MULTIPLIER
                * std20
            )
        )

        band_width = (
            upper_band
            - lower_band
        )

        percent_b = (
            (
                close
                - lower_band
            )
            / band_width
        )

        true_range = (
            calculate_true_range(
                history
            )
        )

        atr = (
            true_range
            .rolling(
                ATR_PERIOD
            )
            .mean()
        )

        atr_distance = (
            (
                close
                - sma20
            )
            / atr
        )

        latest_close = float(
            close.iloc[-1]
        )

        previous_close = float(
            close.iloc[-2]
        )

        latest_rsi = float(
            rsi.iloc[-1]
        )

        previous_rsi = float(
            rsi.iloc[-2]
        )

        latest_stoch_rsi = float(
            stoch_rsi.iloc[-1]
        )

        latest_mfi = float(
            mfi.iloc[-1]
        )

        latest_percent_b = float(
            percent_b.iloc[-1]
        )

        latest_atr = float(
            atr.iloc[-1]
        )

        latest_atr_distance = float(
            atr_distance.iloc[-1]
        )

        latest_sma20 = float(
            sma20.iloc[-1]
        )

        recent_rsi_min = float(
            rsi
            .tail(5)
            .min()
        )

        trailing_52week = (
            history.tail(
                WEEK_52_SESSIONS
            )
        )

        week_52_high = float(
            trailing_52week[
                "High"
            ].max()
        )

        week_52_low = float(
            trailing_52week[
                "Low"
            ].min()
        )

        drawdown_from_high = (
            (
                week_52_high
                - latest_close
            )
            / week_52_high
            * 100.0
        )

        distance_from_low = (
            (
                latest_close
                - week_52_low
            )
            / week_52_low
            * 100.0
        )

        if (
            week_52_high
            > week_52_low
        ):
            week_52_position = (
                (
                    latest_close
                    - week_52_low
                )
                / (
                    week_52_high
                    - week_52_low
                )
                * 100.0
            )
        else:
            week_52_position = 50.0

        signals = {
            "rsi_oversold": (
                latest_rsi < 30
            ),
            "stoch_rsi_oversold": (
                latest_stoch_rsi < 20
            ),
            "mfi_oversold": (
                latest_mfi < 20
            ),
            "below_lower_bollinger": (
                latest_percent_b < 0
            ),
            "deep_atr_pullback": (
                latest_atr_distance
                <= -1.5
            ),
        }

        signal_count = sum(
            bool(value)
            for value
            in signals.values()
        )

        extension_signals = {
            "rsi_overbought": (
                latest_rsi >= 70
            ),
            "stoch_rsi_overbought": (
                latest_stoch_rsi >= 80
            ),
            "mfi_overbought": (
                latest_mfi >= 80
            ),
            "above_upper_bollinger": (
                latest_percent_b > 1.0
            ),
            "extended_above_sma20": (
                latest_atr_distance
                >= 1.5
            ),
        }

        extension_signal_count = sum(
            bool(value)
            for value
            in extension_signals.values()
        )

        if (
            latest_rsi < 20
            or signal_count >= 4
        ):
            overall_context = (
                "DEEPLY_OVERSOLD"
            )

        elif (
            latest_rsi >= 80
            or extension_signal_count >= 4
        ):
            overall_context = (
                "OVERBOUGHT"
            )

        elif signal_count >= 2:
            overall_context = (
                "OVERSOLD"
            )

        elif extension_signal_count >= 2:
            overall_context = (
                "EXTENDED"
            )

        elif signal_count == 1:
            overall_context = (
                "PULLBACK"
            )

        else:
            overall_context = (
                "NORMAL"
            )

        recovery_state = (
            classify_recovery_state(
                overall_context=(
                    overall_context
                ),
                current_close=(
                    latest_close
                ),
                previous_close=(
                    previous_close
                ),
                current_rsi=(
                    latest_rsi
                ),
                previous_rsi=(
                    previous_rsi
                ),
                recent_rsi_min=(
                    recent_rsi_min
                ),
            )
        )

        return {
            "symbol": (
                normalized_symbol
            ),
            "measurement_date": (
                measurement_date
            ),
            "status": "AVAILABLE",
            "reason": "",
            "data_source": (
                data_source
            ),
            "close": round(
                latest_close,
                4,
            ),
            "rsi_14": round(
                latest_rsi,
                4,
            ),
            "rsi_state": (
                classify_rsi(
                    latest_rsi
                )
            ),
            "stoch_rsi_14": round(
                latest_stoch_rsi,
                4,
            ),
            "stoch_rsi_state": (
                classify_stoch_rsi(
                    latest_stoch_rsi
                )
            ),
            "mfi_14": round(
                latest_mfi,
                4,
            ),
            "mfi_state": (
                classify_mfi(
                    latest_mfi
                )
            ),
            "bollinger_sma_20": round(
                latest_sma20,
                4,
            ),
            "bollinger_lower": round(
                float(
                    lower_band.iloc[-1]
                ),
                4,
            ),
            "bollinger_upper": round(
                float(
                    upper_band.iloc[-1]
                ),
                4,
            ),
            "bollinger_percent_b": round(
                latest_percent_b,
                4,
            ),
            "bollinger_state": (
                classify_bollinger(
                    latest_percent_b
                )
            ),
            "atr_14": round(
                latest_atr,
                4,
            ),
            "atr_distance_from_sma20": round(
                latest_atr_distance,
                4,
            ),
            "atr_pullback_state": (
                classify_atr_pullback(
                    latest_atr_distance
                )
            ),
            "week_52_high": round(
                week_52_high,
                4,
            ),
            "week_52_low": round(
                week_52_low,
                4,
            ),
            "drawdown_from_52week_high_percent": round(
                drawdown_from_high,
                4,
            ),
            "distance_from_52week_low_percent": round(
                distance_from_low,
                4,
            ),
            "week_52_position_percent": round(
                week_52_position,
                4,
            ),
            "oversold_signals": (
                signals
            ),
            "oversold_signal_count": (
                signal_count
            ),
            "extension_signals": (
                extension_signals
            ),
            "extension_signal_count": (
                extension_signal_count
            ),
            "overall_context": (
                overall_context
            ),
            "recovery_state": (
                recovery_state
            ),
            "research_only": True,
        }

    except Exception as error:
        return {
            "symbol": (
                normalized_symbol
            ),
            "measurement_date": (
                measurement_date
            ),
            "status": "UNAVAILABLE",
            "reason": str(
                error
            ),
            "data_source": (
                "UNAVAILABLE"
            ),
        }
