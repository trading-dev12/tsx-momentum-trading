"""
Northstar Headless Scanner

Provides one GUI-independent scanner cycle using the same
market-data and strategy components as the workstation.

IMPORTANT:
Importing this module does NOT start scanning.
"""

import json
from datetime import datetime
from pathlib import Path

from core.config_loader import load_settings
from core.market_context import score_market_context
from core.market_data import get_quotes
from core.watchlist_loader import load_all_watchlists
from paper_trading.automatic_eod import (
    run_52_week_shadow_scan,
    run_mean_reversion_shadow_scan,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RUNTIME_FOLDER = (
    PROJECT_ROOT
    / "data"
    / "runtime"
)

SCANNER_SNAPSHOT_FILE = (
    RUNTIME_FOLDER
    / "latest_scanner_snapshot.json"
)

SCANNER_HEALTH_FILE = (
    RUNTIME_FOLDER
    / "scanner_health.json"
)


def make_json_safe(value):
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    return str(value)


def normalize_strategy_quote(quote):
    strategy = quote.get(
        "strategy",
        "MOMENTUM",
    )

    price = float(
        quote.get(
            "price",
            quote.get("close", 0),
        )
        or 0
    )

    if strategy == "52_WEEK_BREAKOUT":
        return {
            "symbol": quote["symbol"],
            "strategy": strategy,
            "price": price,
            "close": price,
            "tmqs": float(
                quote.get("tmqs", 0)
                or 0
            ),
            "confidence_score": 0,
            "relative_volume": float(
                quote.get("rvol", 0)
                or 0
            ),
            "grades": {
                "RVOL": "N/A",
                "Momentum": "N/A",
                "Liquidity": "N/A",
            },
            "breakout_status": (
                "52-WEEK BREAKOUT"
                if quote.get("breakout")
                else "BELOW 52-WEEK HIGH"
            ),
            "decision": quote["decision"],
            "reason": quote.get(
                "reason",
                "",
            ),
        }

    if strategy == "MEAN_REVERSION":
        return {
            "symbol": quote["symbol"],
            "strategy": strategy,
            "price": price,
            "close": price,
            "tmqs": 0.0,
            "confidence_score": 0,
            "relative_volume": 0.0,
            "grades": {
                "RVOL": "N/A",
                "Momentum": "N/A",
                "Liquidity": "N/A",
            },
            "breakout_status": (
                f"RSI-2: "
                f"{float(quote.get('rsi_2', 0) or 0):.1f}"
            ),
            "decision": quote["decision"],
            "reason": quote.get(
                "reason",
                "",
            ),
        }

    normalized = dict(quote)

    normalized.setdefault(
        "strategy",
        "MOMENTUM",
    )

    normalized.setdefault(
        "price",
        price,
    )

    normalized.setdefault(
        "close",
        price,
    )

    return normalized


def save_scanner_snapshot(
    quotes,
    view="LIVE",
    snapshot_file=SCANNER_SNAPSHOT_FILE,
    generated_at=None,
):
    if not quotes:
        return None

    snapshot_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if generated_at is None:
        generated_at = datetime.now().isoformat(
            timespec="seconds"
        )

    snapshot = {
        "generated_at": generated_at,
        "view": view,
        "quotes": make_json_safe(
            quotes
        ),
    }

    temporary_file = (
        snapshot_file.with_suffix(
            ".tmp"
        )
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            snapshot,
            file,
            indent=4,
        )

    temporary_file.replace(
        snapshot_file
    )

    return snapshot


def write_scanner_health(
    status,
    last_successful_refresh,
    refresh_id,
    worker="IDLE",
    health_file=SCANNER_HEALTH_FILE,
    heartbeat=None,
):
    health_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if heartbeat is None:
        heartbeat = datetime.now().isoformat()

    health = {
        "status": status,
        "heartbeat": heartbeat,
        "last_successful_refresh": (
            last_successful_refresh
        ),
        "refresh_id": refresh_id,
        "worker": worker,
    }

    with health_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            health,
            file,
            indent=4,
        )

    return health


def run_headless_scanner_cycle(
    refresh_id,
    settings_provider=load_settings,
    watchlist_provider=load_all_watchlists,
    market_provider=score_market_context,
    quote_provider=get_quotes,
    breakout_provider=run_52_week_shadow_scan,
    mean_reversion_provider=run_mean_reversion_shadow_scan,
    snapshot_file=SCANNER_SNAPSHOT_FILE,
    health_file=SCANNER_HEALTH_FILE,
    current_datetime=None,
):
    settings_provider()

    watchlist = watchlist_provider()

    market = market_provider()

    momentum_quotes = quote_provider(
        watchlist
    )

    breakout_scan = breakout_provider()

    mean_reversion_scan = (
        mean_reversion_provider()
    )

    breakout_quotes = (
        breakout_scan["results"]["ready"]
        + breakout_scan["results"]["watch"]
    )

    mean_reversion_quotes = (
        mean_reversion_scan["results"]["ready"]
        + mean_reversion_scan["results"]["watch"]
    )

    combined_quotes = list(
        momentum_quotes
    )

    combined_quotes.extend(
        normalize_strategy_quote(quote)
        for quote in breakout_quotes
    )

    combined_quotes.extend(
        normalize_strategy_quote(quote)
        for quote in mean_reversion_quotes
    )

    if current_datetime is None:
        current_datetime = datetime.now()

    generated_at = (
        current_datetime.isoformat(
            timespec="seconds"
        )
    )

    last_successful_refresh = (
        current_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    save_scanner_snapshot(
        combined_quotes,
        view="LIVE",
        snapshot_file=snapshot_file,
        generated_at=generated_at,
    )

    write_scanner_health(
        status="RUNNING",
        last_successful_refresh=(
            last_successful_refresh
        ),
        refresh_id=refresh_id,
        worker="IDLE",
        health_file=health_file,
        heartbeat=(
            current_datetime.isoformat()
        ),
    )

    return {
        "status": "COMPLETED",
        "refresh_id": refresh_id,
        "market": market,
        "quotes": combined_quotes,
        "momentum_count": len(
            momentum_quotes
        ),
        "breakout_count": len(
            breakout_quotes
        ),
        "mean_reversion_count": len(
            mean_reversion_quotes
        ),
        "last_successful_refresh": (
            last_successful_refresh
        ),
    }
