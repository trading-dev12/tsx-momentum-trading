from __future__ import annotations

import ast
from pathlib import Path


TARGET = Path("core/market_data.py")
BACKUP = Path("core/market_data.py.before_ibkr_live_integration")

NEW_FUNCTIONS = '''def get_live_quote(symbol, live_quote=None):
    """
    Build the complete scanner record for one symbol.

    IBKR supplies live price and current volume when available.
    Yahoo remains responsible for historical indicators and is
    used as the live-data fallback.
    """

    try:
        data_source = "YAHOO_FALLBACK"
        price_source = "YAHOO_FAST_INFO"

        ibkr_price = 0.0
        ibkr_volume = 0.0

        if live_quote is not None:
            ibkr_price = float(
                live_quote.get("price", 0) or 0
            )
            ibkr_volume = float(
                live_quote.get("volume", 0) or 0
            )

        if ibkr_price > 0:
            price = ibkr_price
            volume = ibkr_volume
            data_source = "IBKR"
            price_source = live_quote.get(
                "price_source",
                "UNKNOWN",
            )
        else:
            yahoo_symbol = (
                symbol
                if symbol.endswith(".TO")
                else symbol + ".TO"
            )

            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.fast_info

            price = float(
                info.get("lastPrice", 0) or 0
            )
            volume = float(
                info.get("lastVolume", 0) or 0
            )

        if price <= 0:
            raise ValueError(
                f"No usable live price received for {symbol}."
            )

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
            change_percent = (
                (price - previous_close)
                / previous_close
            ) * 100
            gap_percent = change_percent
        else:
            change_percent = 0
            gap_percent = 0

        average_volume = get_average_volume(symbol)
        atr = calculate_live_atr(symbol)

        breakout_metrics = (
            get_52_week_breakout_metrics(symbol)
        )

        mean_reversion_metrics = (
            get_mean_reversion_metrics(symbol)
        )

        if average_volume > 0:
            relative_volume = round(
                volume / average_volume,
                2,
            )
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
            "prior_52_week_high": breakout_metrics[
                "prior_52_week_high"
            ],
            "sma_50": breakout_metrics["sma_50"],
            "sma_200": breakout_metrics["sma_200"],
            "sma_20": mean_reversion_metrics["sma_20"],
            "rsi_2": mean_reversion_metrics["rsi_2"],
            "rsi_14": mean_reversion_metrics["rsi_14"],
            "bollinger_lower": mean_reversion_metrics[
                "bollinger_lower"
            ],
            "atr": atr,
            "rvol_status": get_rvol_status(
                relative_volume
            ),
            "status": (
                "Live IBKR Data"
                if data_source == "IBKR"
                else "Yahoo Fallback Data"
            ),
            "data_source": data_source,
            "price_source": price_source,
        }

        quote["score"] = calculate_score(quote)
        quote["grades"] = grade_stock(quote)
        quote["tmqs"] = calculate_tmqs(quote)

        quote["breakout_status"] = (
            get_breakout_status(quote)
        )

        quote["confidence_score"] = (
            calculate_confidence_score(quote)
        )

        decision, reason = get_trade_decision(quote)

        quote["decision"] = decision
        quote["reason"] = reason

        breakout_52week_input = (
            build_breakout_52week_input(quote)
        )

        breakout_52week_result = (
            Breakout52WeekStrategy().evaluate(
                breakout_52week_input
            )
        )

        quote["breakout_52week_decision"] = (
            breakout_52week_result.decision.value
        )
        quote["breakout_52week_reason"] = (
            breakout_52week_result.reason
        )
        quote["breakout_52week"] = (
            breakout_52week_result.breakout
        )

        return quote

    except Exception as error:
        print(f"Skipping {symbol}: {error}")
        return None


def get_quotes(watchlist):
    """
    Retrieve one batch of live IBKR quotes and build full
    scanner records.

    Yahoo live data is used only if IBKR is unavailable or an
    individual IBKR quote fails.
    """

    symbols = list(watchlist)
    quotes = []

    ibkr_quotes = {}
    ibkr_errors = {}

    provider = IBKRDataProvider(client_id=14)

    try:
        ibkr_quotes, ibkr_errors = provider.get_quotes(
            symbols
        )

        print(
            "IBKR live quote batch: "
            f"{len(ibkr_quotes)}/{len(symbols)} received."
        )

        if ibkr_errors:
            print(
                "IBKR individual quote fallbacks: "
                f"{len(ibkr_errors)}"
            )

    except Exception as error:
        print(
            "IBKR batch unavailable. "
            f"Using Yahoo live fallback: {error}"
        )
        ibkr_quotes = {}

    finally:
        provider.disconnect()

    for symbol in symbols:
        quote = get_live_quote(
            symbol,
            live_quote=ibkr_quotes.get(symbol),
        )

        if quote is not None:
            quotes.append(quote)

    decision_rank = {
        "READY": 3,
        "WATCH": 2,
        "IGNORE": 1,
    }

    quotes.sort(
        key=lambda quote: (
            decision_rank.get(
                quote["decision"],
                0,
            ),
            quote["tmqs"],
            quote.get(
                "confidence_score",
                0,
            ),
        ),
        reverse=True,
    )

    return quotes
'''


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")

    tree = ast.parse(source)

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    live_function = functions.get("get_live_quote")
    quotes_function = functions.get("get_quotes")

    if live_function is None or quotes_function is None:
        raise RuntimeError(
            "Could not find both get_live_quote() and "
            "get_quotes(). No changes were made."
        )

    if live_function.lineno >= quotes_function.lineno:
        raise RuntimeError(
            "Unexpected function order. No changes were made."
        )

    lines = source.splitlines(keepends=True)

    start_index = live_function.lineno - 1
    end_index = quotes_function.end_lineno

    updated_lines = (
        lines[:start_index]
        + [NEW_FUNCTIONS.rstrip() + "\n"]
        + lines[end_index:]
    )

    updated = "".join(updated_lines)

    import_line = (
        "from core.ibkr_data_provider "
        "import IBKRDataProvider\n"
    )

    if import_line not in updated:
        insertion_marker = "import yfinance as yf\n"

        if insertion_marker not in updated:
            raise RuntimeError(
                "Could not locate yfinance import. "
                "No changes were made."
            )

        updated = updated.replace(
            insertion_marker,
            insertion_marker + import_line,
            1,
        )

    ast.parse(updated)

    BACKUP.write_text(source, encoding="utf-8")
    TARGET.write_text(updated, encoding="utf-8")

    print(f"Backup created: {BACKUP}")
    print(f"Updated: {TARGET}")
    print("IBKR live-data patch applied successfully.")


if __name__ == "__main__":
    main()
