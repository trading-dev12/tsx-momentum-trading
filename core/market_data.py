from datetime import datetime, timedelta
from shlex import quote
from zoneinfo import ZoneInfo
import yfinance as yf

from core.previous_day import get_previous_day
from scanner.momentum_score import calculate_score
from scanner.stock_grader import grade_stock
from scanner.tmqs_score import calculate_tmqs
from rules.trade_decision import get_trade_decision
from strategies.breakout_52week_adapter import build_breakout_52week_input
from strategies.breakout_52week_strategy import Breakout52WeekStrategy
from scanner.confidence_score import calculate_confidence_score

def get_breakout_status(quote):
    price = quote.get("price", 0)
    previous_high = quote.get("previous_high", 0)
    previous_close = quote.get("previous_close", 0)

    if price <= 0 or previous_high <= 0 or previous_close <= 0:
        return "UNKNOWN"

    if price > previous_high:
        return "BREAKOUT"

    if price >= previous_high * 0.995:
        return "NEAR BREAKOUT"

    if price >= previous_close:
        return "INSIDE RANGE"

    return "WEAK / BELOW CLOSE"


def get_average_volume(symbol, days=20):
    try:
        yahoo_symbol = symbol if symbol.endswith(".TO") else symbol + ".TO"
        ticker = yf.Ticker(yahoo_symbol)
        history = ticker.history(period="30d")

        if history.empty or "Volume" not in history:
            return 0

        volumes = history["Volume"].tail(days)
        return int(volumes.mean())

    except Exception:
        return 0
def get_52_week_breakout_metrics(symbol):
    """
    Return the completed-session data required by the 52-week breakout strategy.

    Today's partial daily candle is excluded by requesting history only through
    the current Toronto date. Yahoo Finance treats the end date as exclusive.
    """

    empty_metrics = {
        "prior_52_week_high": 0.0,
        "sma_50": 0.0,
        "sma_200": 0.0,
    }

    try:
        yahoo_symbol = symbol if symbol.endswith(".TO") else symbol + ".TO"

        today = datetime.now(ZoneInfo("America/Toronto")).date()
        start_date = today - timedelta(days=800)

        history = yf.Ticker(yahoo_symbol).history(
            start=start_date.isoformat(),
            end=today.isoformat(),
            interval="1d",
            auto_adjust=False,
        )

        if history is None or history.empty:
            return empty_metrics

        if "High" not in history.columns or "Close" not in history.columns:
            return empty_metrics

        history = history.dropna(subset=["High", "Close"])

        if history.empty:
            return empty_metrics

        prior_high_window = history["High"].tail(252)
        prior_52_week_high = float(prior_high_window.max())

        sma_50 = (
            float(history["Close"].tail(50).mean())
            if len(history) >= 50
            else 0.0
        )

        sma_200 = (
            float(history["Close"].tail(200).mean())
            if len(history) >= 200
            else 0.0
        )

        return {
            "prior_52_week_high": prior_52_week_high,
            "sma_50": sma_50,
            "sma_200": sma_200,
        }

    except Exception as error:
        print(f"52-week metrics unavailable for {symbol}: {error}")
        return empty_metrics


def get_mean_reversion_metrics(symbol):
    """
    Return completed-session indicators required by the research-only
    mean reversion strategy.

    Today's partial daily candle is excluded.
    """

    empty_metrics = {
        "sma_20": 0.0,
        "rsi_2": 0.0,
        "rsi_14": 0.0,
        "bollinger_lower": 0.0,
    }

    try:
        yahoo_symbol = symbol if symbol.endswith(".TO") else symbol + ".TO"

        today = datetime.now(ZoneInfo("America/Toronto")).date()
        start_date = today - timedelta(days=120)

        history = yf.Ticker(yahoo_symbol).history(
            start=start_date.isoformat(),
            end=today.isoformat(),
            interval="1d",
            auto_adjust=False,
        )

        if history is None or history.empty:
            return empty_metrics

        if "Close" not in history.columns:
            return empty_metrics

        closes = history["Close"].dropna()

        if len(closes) < 20:
            return empty_metrics

        sma_20 = float(
            closes.rolling(window=20).mean().iloc[-1]
        )

        standard_deviation_20 = float(
            closes.rolling(window=20).std().iloc[-1]
        )

        bollinger_lower = sma_20 - (2 * standard_deviation_20)

        price_change = closes.diff()
        gains = price_change.clip(lower=0)
        losses = -price_change.clip(upper=0)

        def calculate_rsi(period):
            average_gain = gains.ewm(
                alpha=1 / period,
                adjust=False,
                min_periods=period,
            ).mean()

            average_loss = losses.ewm(
                alpha=1 / period,
                adjust=False,
                min_periods=period,
            ).mean()

            latest_gain = average_gain.iloc[-1]
            latest_loss = average_loss.iloc[-1]

            if latest_loss == 0:
                return 100.0

            relative_strength = latest_gain / latest_loss

            return 100 - (
                100 / (1 + relative_strength)
            )

        rsi_2 = float(calculate_rsi(2))
        rsi_14 = float(calculate_rsi(14))

        return {
            "sma_20": round(sma_20, 4),
            "rsi_2": round(rsi_2, 4),
            "rsi_14": round(rsi_14, 4),
            "bollinger_lower": round(bollinger_lower, 4),
        }

    except Exception as error:
    
        print(f"Mean reversion metrics unavailable for {symbol}: {error}")
        return empty_metrics


def get_rvol_status(relative_volume):
    if relative_volume >= 2:
        return "HIGH"

    if relative_volume >= 1:
        return "NORMAL"

    return "LOW"

def calculate_live_atr(symbol, period=14):
    """
    Calculate the current Average True Range using daily price history.
    """

    try:
        yahoo_symbol = symbol if symbol.endswith(".TO") else symbol + ".TO"

        history = yf.Ticker(yahoo_symbol).history(
            period="2mo",
            interval="1d",
            auto_adjust=False,
        )

        if history is None or len(history) < period + 1:
            return 0.0

        previous_close = history["Close"].shift(1)

        history["high_low_range"] = (
            history["High"] - history["Low"]
        )

        history["high_previous_close_range"] = (
            history["High"] - previous_close
        ).abs()

        history["low_previous_close_range"] = (
            history["Low"] - previous_close
        ).abs()

        true_range = history[
            [
                "high_low_range",
                "high_previous_close_range",
                "low_previous_close_range",
            ]
        ].max(axis=1)

        atr = true_range.rolling(window=period).mean().iloc[-1]

        if atr != atr:
            return 0.0

        return round(float(atr), 2)

    except Exception as error:
        print(f"ATR unavailable for {symbol}: {error}")
        return 0.0
    
def get_live_quote(symbol):
    try:
        yahoo_symbol = symbol if symbol.endswith(".TO") else symbol + ".TO"
        ticker = yf.Ticker(yahoo_symbol)
        info = ticker.fast_info

        price = info.get("lastPrice", 0) or 0
        volume = info.get("lastVolume", 0) or 0

        previous_day = get_previous_day(symbol)

        if previous_day:
            previous_close = previous_day["previous_close"]
            previous_high = previous_day["previous_high"]
            previous_low = previous_day["previous_low"]
        else:
            previous_close = 0
            previous_high = 0
            previous_low = 0

        if previous_close:
            change_percent = ((price - previous_close) / previous_close) * 100
            gap_percent = change_percent
        else:
            change_percent = 0
            gap_percent = 0

        average_volume = get_average_volume(symbol)
        atr = calculate_live_atr(symbol)
        breakout_metrics = get_52_week_breakout_metrics(symbol)
        mean_reversion_metrics = get_mean_reversion_metrics(symbol)

        if average_volume > 0:
            relative_volume = round(volume / average_volume, 2)
        else:
            relative_volume = 0

        quote = {
            "symbol": symbol,
            "price": price,
            "previous_high": previous_high,
            "previous_low": previous_low,
            "previous_close": previous_close,
            "gap_percent": gap_percent,
            "change_percent": change_percent,
            "volume": volume,
            "average_volume": average_volume,
            "relative_volume": relative_volume,
            "prior_52_week_high": breakout_metrics["prior_52_week_high"],
            "sma_50": breakout_metrics["sma_50"],
            "sma_200": breakout_metrics["sma_200"],
            "sma_20": mean_reversion_metrics["sma_20"],
            "rsi_2": mean_reversion_metrics["rsi_2"],
            "rsi_14": mean_reversion_metrics["rsi_14"],
            "bollinger_lower": mean_reversion_metrics["bollinger_lower"],
            "atr": atr,
            "rvol_status": get_rvol_status(relative_volume),
            "status": "Live Data",
        }

        quote["score"] = calculate_score(quote)
        quote["grades"] = grade_stock(quote)
        quote["tmqs"] = calculate_tmqs(quote)
        quote["breakout_status"] = get_breakout_status(quote)
        quote["confidence_score"] = calculate_confidence_score(quote)
        decision, reason = get_trade_decision(quote)

        quote["decision"] = decision
        quote["reason"] = reason

        breakout_52week_input = build_breakout_52week_input(quote)
        breakout_52week_result = Breakout52WeekStrategy().evaluate(
        breakout_52week_input
        )

        quote["breakout_52week_decision"] = breakout_52week_result.decision.value
        quote["breakout_52week_reason"] = breakout_52week_result.reason
        quote["breakout_52week"] = breakout_52week_result.breakout

        return quote

    except Exception as error:
        print(f"Skipping {symbol}: {error}")
        return None


def get_quotes(watchlist):
    quotes = []

    for symbol in watchlist:
        quote = get_live_quote(symbol)

        if quote is not None:
            quotes.append(quote)

    decision_rank = {
    "READY": 3,
    "WATCH": 2,
    "IGNORE": 1,
}

    quotes.sort(
    key=lambda quote: (
        decision_rank.get(quote["decision"], 0),
        quote["tmqs"],
        quote.get("confidence_score", 0),
    ),
    reverse=True,
)    

    return quotes