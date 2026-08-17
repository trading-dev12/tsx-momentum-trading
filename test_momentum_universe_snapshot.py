import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from core.eod_signal_service import (
    build_eod_signal_from_rows,
)
from research.momentum_universe_snapshot import (
    build_momentum_universe_rows,
    save_momentum_universe_snapshot,
)


def make_signal(
    symbol,
    decision,
    tmqs,
    rvol,
):
    return {
        "symbol": symbol,
        "strategy": "MOMENTUM",
        "signal_date": "2026-08-17",
        "open": 100.0,
        "high": 103.0,
        "low": 99.0,
        "close": 102.0,
        "volume": 2_000_000,
        "previous_open": 98.0,
        "previous_high": 101.0,
        "previous_low": 97.0,
        "previous_close": 99.0,
        "previous_volume": 1_000_000,
        "gap_percent": 1.010101,
        "price_change_percent": 3.030303,
        "breakout_percent": 0.990099,
        "dollar_volume": 204_000_000.0,
        "atr": 2.0,
        "atr_percent": 1.960784,
        "tmqs": tmqs,
        "rvol": rvol,
        "breakout": "BREAKOUT",
        "decision": decision,
        "reason": "test",
        "breakout_score": 25.0,
        "volume_score": 24.0,
        "price_score": 25.0,
        "data_source": "YAHOO_DAILY_EOD",
    }


def test_build_snapshot_keeps_entire_momentum_universe():
    results = {
        "ready": [
            make_signal(
                "AAA.TO",
                "READY",
                90,
                2.0,
            )
        ],
        "watch": [
            make_signal(
                "BBB.TO",
                "WATCH",
                70,
                1.2,
            )
        ],
        "ignore": [
            make_signal(
                "CCC.TO",
                "IGNORE",
                40,
                0.5,
            )
        ],
        "errors": [
            {
                "symbol": "DDD.TO",
                "error": "Data unavailable",
            }
        ],
    }

    rows = build_momentum_universe_rows(
        results,
        signal_date="2026-08-17",
        captured_at=datetime(
            2026,
            8,
            17,
            16,
            5,
            tzinfo=ZoneInfo(
                "America/Toronto"
            ),
        ),
    )

    assert len(rows) == 4

    assert [
        row["symbol"]
        for row in rows[:3]
    ] == [
        "AAA.TO",
        "BBB.TO",
        "CCC.TO",
    ]

    assert [
        row["daily_rank"]
        for row in rows[:3]
    ] == [1, 2, 3]

    assert rows[0]["breakout_score"] == 25.0
    assert rows[0]["volume_score"] == 24.0
    assert rows[0]["price_score"] == 25.0
    assert rows[0]["previous_close"] == 99.0
    assert rows[0]["capture_status"] == "OK"

    assert rows[3]["symbol"] == "DDD.TO"
    assert rows[3]["decision"] == "ERROR"
    assert rows[3]["capture_status"] == "ERROR"
    assert (
        rows[3]["error_message"]
        == "Data unavailable"
    )


def test_snapshot_is_written_atomically_to_daily_csv(
    tmp_path,
):
    results = {
        "ready": [
            make_signal(
                "AAA.TO",
                "READY",
                90,
                2.0,
            )
        ],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    result = save_momentum_universe_snapshot(
        results=results,
        signal_date="2026-08-17",
        output_directory=tmp_path,
    )

    assert result["success"] is True
    assert result["rows_saved"] == 1
    assert result["error_rows"] == 0

    output_path = (
        tmp_path
        / "2026-08-17.csv"
    )

    assert output_path.exists()
    assert not (
        tmp_path
        / "2026-08-17.csv.tmp"
    ).exists()

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAA.TO"
    assert rows[0]["decision"] == "READY"
    assert rows[0]["daily_rank"] == "1"
    assert (
        rows[0]["data_source"]
        == "YAHOO_DAILY_EOD"
    )


def test_authoritative_eod_signal_retains_raw_inputs():
    rows = []

    for index in range(15):
        close = 100.0 + index

        rows.append(
            {
                "date": (
                    f"2026-07-{index + 1:02d}"
                ),
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": (
                    1_000_000
                    + (index * 100_000)
                ),
            }
        )

    signal = build_eod_signal_from_rows(
        "TEST.TO",
        rows,
    )

    assert signal is not None
    assert signal["strategy"] == "MOMENTUM"
    assert signal["signal_date"] == "2026-07-15"
    assert signal["open"] == 113.5
    assert signal["high"] == 115.0
    assert signal["low"] == 113.0
    assert signal["close"] == 114.0
    assert signal["volume"] == 2_400_000
    assert signal["previous_close"] == 113.0
    assert signal["previous_high"] == 114.0
    assert signal["previous_volume"] == 2_300_000
    assert "gap_percent" in signal
    assert "price_change_percent" in signal
    assert "breakout_percent" in signal
    assert "atr_percent" in signal
    assert "dollar_volume" in signal
    assert "breakout_score" in signal
    assert "volume_score" in signal
    assert "price_score" in signal
    assert (
        signal["data_source"]
        == "YAHOO_DAILY_EOD"
    )
