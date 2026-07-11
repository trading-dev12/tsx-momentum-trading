"""
Paper Trading Opening Price Provider

Retrieves the first available regular-session opening price for
a requested symbol and trading date.

For recent dates, the provider first tries Yahoo Finance
one-minute data so a paper trade can execute shortly after the
market opens.

If one-minute data is unavailable, it falls back to an exact
daily bar. No previous trading-day price is ever substituted.
"""

from datetime import date, datetime, timedelta

import yfinance as yf


def normalize_symbol(symbol):
    """
    Convert a TSX symbol into Yahoo Finance format.
    """

    normalized_symbol = str(symbol).strip().upper()

    if not normalized_symbol.endswith(".TO"):
        normalized_symbol = f"{normalized_symbol}.TO"

    return normalized_symbol


def normalize_date(date_value):
    """
    Convert a date, datetime, or ISO date string into a date.
    """

    if isinstance(date_value, datetime):
        return date_value.date()

    if isinstance(date_value, date):
        return date_value

    return datetime.strptime(
        str(date_value),
        "%Y-%m-%d",
    ).date()


def get_row_date(index_value):
    """
    Convert a Yahoo Finance row index into a calendar date.
    """

    if hasattr(index_value, "date"):
        return index_value.date()

    return datetime.strptime(
        str(index_value)[:10],
        "%Y-%m-%d",
    ).date()


def read_open_value(value):
    """
    Convert either a scalar or one-item pandas Series into float.
    """

    if hasattr(value, "iloc"):
        value = value.iloc[0]

    return float(value)


def build_failure(symbol, trading_date, message):
    """
    Build a consistent failed price response.
    """

    return {
        "success": False,
        "symbol": symbol,
        "trading_date": trading_date,
        "message": message,
    }


def find_matching_open(history, requested_date):
    """
    Find the first row that exactly matches requested_date.
    """

    if history is None or history.empty:
        return None

    for row_index, row in history.iterrows():
        if get_row_date(row_index) != requested_date:
            continue

        try:
            open_price = read_open_value(row["Open"])
        except (
            KeyError,
            TypeError,
            ValueError,
            IndexError,
        ):
            continue

        if open_price > 0:
            return open_price

    return None


def get_intraday_open_price(
    yahoo_symbol,
    requested_date,
):
    """
    Retrieve the first regular-session one-minute opening price.
    """

    requested_date_text = requested_date.isoformat()

    try:
        history = yf.Ticker(yahoo_symbol).history(
            period="7d",
            interval="1m",
            auto_adjust=False,
            prepost=False,
        )

    except Exception:
        return None

    return find_matching_open(
        history,
        requested_date,
    )


def get_daily_open_price(
    yahoo_symbol,
    requested_date,
):
    """
    Retrieve an exact daily opening price as a fallback.
    """

    start_date = requested_date.isoformat()

    end_date = (
        requested_date + timedelta(days=1)
    ).isoformat()

    try:
        history = yf.download(
            yahoo_symbol,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=False,
            progress=False,
        )

    except Exception:
        return None

    return find_matching_open(
        history,
        requested_date,
    )


def get_market_open_price(symbol, trading_date):
    """
    Return the first available opening price for the exact date.

    Recent-date priority:
        1. First regular-session one-minute candle
        2. Exact daily candle

    Weekend, holiday, missing-date, and unavailable-price
    requests return success=False.
    """

    yahoo_symbol = normalize_symbol(symbol)
    requested_date = normalize_date(trading_date)
    requested_date_text = requested_date.isoformat()

    open_price = get_intraday_open_price(
        yahoo_symbol,
        requested_date,
    )

    price_source = "ONE_MINUTE_OPEN"

    if open_price is None:
        open_price = get_daily_open_price(
            yahoo_symbol,
            requested_date,
        )

        price_source = "DAILY_OPEN"

    if open_price is None:
        return build_failure(
            yahoo_symbol,
            requested_date_text,
            (
                "No exact market opening price is available for "
                f"{requested_date_text}."
            ),
        )

    return {
        "success": True,
        "symbol": yahoo_symbol,
        "trading_date": requested_date_text,
        "open_price": round(open_price, 4),
        "price_source": price_source,
    }