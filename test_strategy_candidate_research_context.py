import csv
from types import SimpleNamespace

import scanner.breakout_52week_scanner as breakout
import scanner.mean_reversion_scanner as mr


def rich_quote():
    return {
        "symbol": "TEST.TO",
        "price": 105.0,
        "last": 105.0,
        "bid": 104.95,
        "ask": 105.05,
        "quote_timestamp": (
            "2026-08-18T16:05:00-04:00"
        ),
        "data_source": "IBKR",
        "price_source": "LAST",
        "previous_close": 102.0,
        "previous_high": 103.0,
        "previous_low": 100.0,
        "gap_percent": 2.941176,
        "change_percent": 2.941176,
        "volume": 1500000,
        "average_volume": 750000,
        "relative_volume": 2.0,
        "prior_52_week_high": 104.0,
        "sma_20": 101.0,
        "sma_50": 100.0,
        "sma_200": 90.0,
        "rsi_2": 8.0,
        "rsi_14": 45.0,
        "bollinger_lower": 99.0,
        "atr": 2.1,
        "score": 91,
        "tmqs": 92,
        "confidence_score": 94,
        "rvol_status": "HIGH",
        "breakout_status": "BREAKOUT",
        "grades": {
            "Momentum": "A",
            "Liquidity": "A",
            "RVOL": "A",
        },
    }


def test_52_week_preserves_existing_quote_context(
    monkeypatch,
):
    monkeypatch.setattr(
        breakout,
        "get_live_quote",
        lambda symbol: rich_quote(),
    )

    monkeypatch.setattr(
        breakout,
        "build_breakout_52week_input",
        lambda quote: quote,
    )

    class FakeStrategy:
        def evaluate(self, data):
            return SimpleNamespace(
                decision=breakout.Decision.READY,
                reason="Research context test",
                breakout=True,
            )

    monkeypatch.setattr(
        breakout,
        "Breakout52WeekStrategy",
        FakeStrategy,
    )

    result = (
        breakout.scan_52_week_breakouts(
            ["TEST.TO"],
            signal_date="2026-08-18",
        )
    )

    row = result["ready"][0]

    assert row["live_data_source"] == "IBKR"
    assert row["confidence_score"] == 94
    assert row["momentum_grade"] == "A"
    assert row["rvol_grade"] == "A"

    assert (
        row[
            "distance_to_52_week_high_percent"
        ]
        == 0.961538
    )

    assert (
        row["signal_quote_status"]
        == "AVAILABLE"
    )

    assert row["signal_bid"] == 104.95
    assert row["signal_ask"] == 105.05
    assert row["signal_midpoint"] == 105.0
    assert row["signal_spread_amount"] == 0.1


def test_mean_reversion_preserves_existing_quote_context(
    monkeypatch,
):
    monkeypatch.setattr(
        mr,
        "get_live_quote",
        lambda symbol: rich_quote(),
    )

    monkeypatch.setattr(
        mr,
        "build_mean_reversion_input",
        lambda quote: object(),
    )

    monkeypatch.setattr(
        mr.MeanReversionScanner,
        "evaluate_stock",
        lambda self, symbol, indicator_data: (
            mr.ScanResult(
                symbol=symbol,
                decision="READY",
                reason="Research context test",
            )
        ),
    )

    result = mr.scan_mean_reversion(
        ["TEST.TO"],
        measurement_date="2026-08-18",
    )

    row = result["ready"][0]

    assert row["live_data_source"] == "IBKR"
    assert row["previous_close"] == 102.0
    assert row["average_volume"] == 750000
    assert row["confidence_score"] == 94
    assert row["liquidity_grade"] == "A"

    assert row["sma_50"] == 100.0
    assert row["sma_200"] == 90.0

    assert (
        row["signal_quote_status"]
        == "AVAILABLE"
    )

    assert row["signal_bid"] == 104.95
    assert row["signal_ask"] == 105.05


def test_richer_candidate_context_persists_to_csv(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    quote = rich_quote()

    monkeypatch.setattr(
        mr,
        "get_live_quote",
        lambda symbol: quote,
    )

    monkeypatch.setattr(
        mr,
        "build_mean_reversion_input",
        lambda quote: object(),
    )

    monkeypatch.setattr(
        mr.MeanReversionScanner,
        "evaluate_stock",
        lambda self, symbol, indicator_data: (
            mr.ScanResult(
                symbol=symbol,
                decision="READY",
                reason="Persistence test",
            )
        ),
    )

    results = mr.scan_mean_reversion(
        ["TEST.TO"],
        measurement_date="2026-08-18",
    )

    filename = mr.save_results(
        results,
        measurement_date="2026-08-18",
    )

    with open(
        filename,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        row = next(
            csv.DictReader(file)
        )

    assert row["live_data_source"] == "IBKR"
    assert row["confidence_score"] == "94"

    assert (
        row["signal_quote_status"]
        == "AVAILABLE"
    )

    assert row["signal_bid"] == "104.95"
    assert row["signal_ask"] == "105.05"
    assert row["momentum_grade"] == "A"
