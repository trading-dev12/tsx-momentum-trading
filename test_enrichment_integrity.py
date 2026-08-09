from datetime import date

from research.enrichment_integrity import (
    analyze_enrichment_integrity,
    missing_enrichment_fields,
)


def make_complete_trade(
    symbol="TEST.TO",
    entry_date="2026-08-10",
):
    return {
        "symbol": symbol,
        "entry_date": entry_date,
        "market_regime": "NORMAL",
        "ma_trend_alignment": "BULLISH",
        "gap_bucket": "SMALL_GAP",
        "volatility_regime": "NORMAL",
        "rs_xic_20": "2.5",
        "rs_xiu_20": "2.0",
        "ma_close_vs_sma20_percent": "1.2",
        "ma_close_vs_sma50_percent": "3.4",
        "ma_close_vs_sma200_percent": "8.1",
        "sector_strength_20": "1.5",
        "gap_percent": "0.4",
        "atr_percent": "2.1",
    }


def test_old_incomplete_trade_is_legacy_not_failure():
    trade = {
        "symbol": "OLD.TO",
        "entry_date": "2026-08-09",
    }

    result = analyze_enrichment_integrity(
        [trade],
        monitor_start_date=date(
            2026,
            8,
            10,
        ),
    )

    assert (
        result["legacy_trade_count"]
        == 1
    )

    assert (
        result["monitored_trade_count"]
        == 0
    )

    assert (
        result["integrity_status"]
        == "NO_MONITORED_TRADES_YET"
    )


def test_new_complete_trade_passes():
    trade = make_complete_trade()

    result = analyze_enrichment_integrity(
        [trade]
    )

    assert (
        result["integrity_status"]
        == "PASS"
    )

    assert (
        result[
            "monitored_fully_enriched_count"
        ]
        == 1
    )

    assert (
        result[
            "monitored_incomplete_count"
        ]
        == 0
    )


def test_new_incomplete_trade_fails():
    trade = make_complete_trade()

    trade["sector_strength_20"] = ""

    result = analyze_enrichment_integrity(
        [trade]
    )

    assert (
        result["integrity_status"]
        == "FAIL"
    )

    assert (
        result[
            "monitored_incomplete_count"
        ]
        == 1
    )

    assert (
        result["missing_factor_counts"][
            "sector_strength_20"
        ]
        == 1
    )


def test_invalid_numeric_value_fails():
    trade = make_complete_trade()

    trade["atr_percent"] = "NOT_A_NUMBER"

    missing = missing_enrichment_fields(
        trade
    )

    assert (
        "atr_percent"
        in missing
    )

    result = analyze_enrichment_integrity(
        [trade]
    )

    assert (
        result["integrity_status"]
        == "FAIL"
    )
