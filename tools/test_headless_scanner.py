"""
Safe tests for Northstar headless scanner.

All market-data and strategy providers are mocked.
Temporary files are used for scanner snapshot and health.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock

from core.headless_scanner import (
    normalize_strategy_quote,
    run_headless_scanner_cycle,
)


def test_normalize_52_week_quote():
    quote = {
        "symbol": "SU.TO",
        "strategy": "52_WEEK_BREAKOUT",
        "close": 71.50,
        "tmqs": 95,
        "rvol": 1.8,
        "breakout": True,
        "decision": "READY",
        "reason": "Breakout confirmed",
    }

    result = normalize_strategy_quote(
        quote
    )

    assert result["symbol"] == "SU.TO"
    assert result["strategy"] == "52_WEEK_BREAKOUT"
    assert result["price"] == 71.50
    assert result["relative_volume"] == 1.8
    assert result["breakout_status"] == "52-WEEK BREAKOUT"
    assert result["decision"] == "READY"


def test_normalize_mean_reversion_quote():
    quote = {
        "symbol": "BMO.TO",
        "strategy": "MEAN_REVERSION",
        "close": 189.10,
        "rsi_2": 4.25,
        "decision": "WATCH",
        "reason": "Oversold",
    }

    result = normalize_strategy_quote(
        quote
    )

    assert result["symbol"] == "BMO.TO"
    assert result["strategy"] == "MEAN_REVERSION"
    assert result["price"] == 189.10
    assert result["tmqs"] == 0.0
    assert result["breakout_status"] == "RSI-2: 4.2"
    assert result["decision"] == "WATCH"


def test_headless_scanner_cycle(tmp_path):
    snapshot_file = (
        tmp_path
        / "latest_scanner_snapshot.json"
    )

    health_file = (
        tmp_path
        / "scanner_health.json"
    )

    settings_provider = MagicMock()

    watchlist_provider = MagicMock(
        return_value=[
            "RY.TO",
            "SU.TO",
        ]
    )

    market_provider = MagicMock(
        return_value={
            "status": "GOOD",
            "score": 80,
        }
    )

    quote_provider = MagicMock(
        return_value=[
            {
                "symbol": "RY.TO",
                "price": 201.25,
                "decision": "WATCH",
                "tmqs": 70,
            }
        ]
    )

    breakout_provider = MagicMock(
        return_value={
            "results": {
                "ready": [
                    {
                        "symbol": "SU.TO",
                        "strategy": "52_WEEK_BREAKOUT",
                        "close": 71.50,
                        "tmqs": 95,
                        "rvol": 1.8,
                        "breakout": True,
                        "decision": "READY",
                        "reason": "Breakout confirmed",
                    }
                ],
                "watch": [],
            }
        }
    )

    mean_reversion_provider = MagicMock(
        return_value={
            "results": {
                "ready": [],
                "watch": [
                    {
                        "symbol": "BMO.TO",
                        "strategy": "MEAN_REVERSION",
                        "close": 189.10,
                        "rsi_2": 4.25,
                        "decision": "WATCH",
                        "reason": "Oversold",
                    }
                ],
            }
        }
    )

    now = datetime(
        2026,
        8,
        8,
        15,
        0,
        0,
    )

    result = run_headless_scanner_cycle(
        refresh_id=7,
        settings_provider=settings_provider,
        watchlist_provider=watchlist_provider,
        market_provider=market_provider,
        quote_provider=quote_provider,
        breakout_provider=breakout_provider,
        mean_reversion_provider=(
            mean_reversion_provider
        ),
        snapshot_file=snapshot_file,
        health_file=health_file,
        current_datetime=now,
    )

    settings_provider.assert_called_once_with()
    watchlist_provider.assert_called_once_with()
    market_provider.assert_called_once_with()

    quote_provider.assert_called_once_with(
        [
            "RY.TO",
            "SU.TO",
        ]
    )

    breakout_provider.assert_called_once_with()
    mean_reversion_provider.assert_called_once_with()

    assert result["status"] == "COMPLETED"
    assert result["refresh_id"] == 7
    assert result["momentum_count"] == 1
    assert result["breakout_count"] == 1
    assert result["mean_reversion_count"] == 1
    assert len(result["quotes"]) == 3

    with snapshot_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    assert snapshot["generated_at"] == (
        "2026-08-08T15:00:00"
    )
    assert snapshot["view"] == "LIVE"
    assert len(snapshot["quotes"]) == 3

    with health_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        health = json.load(file)

    assert health["status"] == "RUNNING"
    assert health["refresh_id"] == 7
    assert health["worker"] == "IDLE"
    assert health["last_successful_refresh"] == (
        "2026-08-08 15:00:00"
    )
