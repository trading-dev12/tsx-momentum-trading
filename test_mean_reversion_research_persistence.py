import csv
from pathlib import Path

from scanner.mean_reversion_scanner import (
    save_results,
)


def test_mean_reversion_daily_csv_keeps_complete_signal_fields(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    record = {
        "symbol": "TEST.TO",
        "strategy": "MEAN_REVERSION",
        "signal_date": "2026-08-17",
        "decision": "READY",
        "reason": "Research test",
        "close": 10.0,
        "price": 10.0,
        "atr": 0.75,
        "tmqs": 82.0,
        "rvol": 1.6,
        "breakout": "INSIDE RANGE",
        "sma_20": 11.0,
        "rsi_2": 5.0,
        "rsi_14": 38.0,
        "bollinger_lower": 10.25,
        "price_vs_sma20_percent": -9.0909,
        "price_vs_lower_band_percent": -2.4390,
    }

    results = {
        "ready": [record],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    report_path = save_results(
        results
    )

    assert report_path is not None

    path = Path(
        report_path
    )

    assert path.exists()

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1

    row = rows[0]

    assert row["signal_date"] == "2026-08-17"
    assert row["close"] == "10.0"
    assert row["atr"] == "0.75"
    assert row["tmqs"] == "82.0"
    assert row["rvol"] == "1.6"
    assert row["breakout"] == "INSIDE RANGE"
    assert row["rsi_2"] == "5.0"
    assert row["rsi_14"] == "38.0"
    assert row["sma_20"] == "11.0"
    assert row["bollinger_lower"] == "10.25"
