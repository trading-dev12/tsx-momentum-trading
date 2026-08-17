from types import SimpleNamespace

import paper_trading.automatic_eod as automatic_eod
import scanner.breakout_52week_scanner as breakout_scanner
import scanner.mean_reversion_scanner as mr_scanner


MEASUREMENT_DATE = "2026-08-14"


def test_52_week_record_uses_explicit_measurement_date(
    monkeypatch,
):
    monkeypatch.setattr(
        breakout_scanner,
        "get_live_quote",
        lambda symbol: {
            "symbol": symbol,
            "price": 100.0,
            "atr": 1.0,
            "tmqs": 80.0,
            "prior_52_week_high": 101.0,
            "average_volume": 500000,
            "relative_volume": 2.0,
            "sma_50": 100.0,
            "sma_200": 90.0,
        },
    )

    monkeypatch.setattr(
        breakout_scanner,
        "build_breakout_52week_input",
        lambda quote: quote,
    )

    class FakeStrategy:
        def evaluate(self, data):
            return SimpleNamespace(
                decision=(
                    breakout_scanner.Decision.IGNORE
                ),
                reason="Research date test",
                breakout=False,
            )

    monkeypatch.setattr(
        breakout_scanner,
        "Breakout52WeekStrategy",
        FakeStrategy,
    )

    results = (
        breakout_scanner.scan_52_week_breakouts(
            ["TEST.TO"],
            signal_date=MEASUREMENT_DATE,
        )
    )

    row = results["ignore"][0]

    assert (
        row["signal_date"]
        == MEASUREMENT_DATE
    )


def test_mean_reversion_record_uses_explicit_measurement_date(
    monkeypatch,
):
    monkeypatch.setattr(
        mr_scanner,
        "get_live_quote",
        lambda symbol: {
            "symbol": symbol,
            "price": 100.0,
            "atr": 1.0,
            "tmqs": 70.0,
            "relative_volume": 1.2,
            "breakout_status": "INSIDE RANGE",
            "sma_20": 102.0,
            "rsi_2": 10.0,
            "rsi_14": 40.0,
            "bollinger_lower": 98.0,
        },
    )

    monkeypatch.setattr(
        mr_scanner,
        "build_mean_reversion_input",
        lambda quote: object(),
    )

    monkeypatch.setattr(
        mr_scanner.MeanReversionScanner,
        "evaluate_stock",
        lambda self, symbol, indicator_data: (
            mr_scanner.ScanResult(
                symbol=symbol,
                decision="IGNORE",
                reason="Research date test",
            )
        ),
    )

    results = (
        mr_scanner.scan_mean_reversion(
            ["TEST.TO"],
            measurement_date=(
                MEASUREMENT_DATE
            ),
        )
    )

    row = results["ignore"][0]

    assert (
        row["signal_date"]
        == MEASUREMENT_DATE
    )


def test_52_week_report_filename_uses_measurement_date(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    results = {
        "ready": [],
        "watch": [],
        "ignore": [
            {
                "symbol": "TEST.TO",
                "signal_date": (
                    MEASUREMENT_DATE
                ),
            }
        ],
        "errors": [],
    }

    report_path = (
        breakout_scanner.save_results(
            results,
            signal_date=MEASUREMENT_DATE,
        )
    )

    assert report_path.endswith(
        f"{MEASUREMENT_DATE}.csv"
    )


def test_mean_reversion_report_filename_uses_measurement_date(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(
        tmp_path
    )

    results = {
        "ready": [],
        "watch": [],
        "ignore": [
            {
                "symbol": "TEST.TO",
                "signal_date": (
                    MEASUREMENT_DATE
                ),
            }
        ],
        "errors": [],
    }

    report_path = (
        mr_scanner.save_results(
            results,
            measurement_date=(
                MEASUREMENT_DATE
            ),
        )
    )

    assert report_path.endswith(
        f"{MEASUREMENT_DATE}.csv"
    )


def test_52_week_eod_wrapper_passes_measurement_date(
    monkeypatch,
):
    observed = {}

    monkeypatch.setattr(
        automatic_eod,
        "load_all_watchlists",
        lambda: ["TEST.TO"],
    )

    def fake_scan(
        watchlist,
        signal_date=None,
    ):
        observed["scan_date"] = (
            signal_date
        )

        return {
            "ready": [],
            "watch": [],
            "ignore": [],
            "errors": [],
        }

    def fake_save(
        results,
        signal_date=None,
    ):
        observed["save_date"] = (
            signal_date
        )

        return "report.csv"

    monkeypatch.setattr(
        automatic_eod,
        "scan_52_week_breakouts",
        fake_scan,
    )

    monkeypatch.setattr(
        automatic_eod,
        "save_52_week_results",
        fake_save,
    )

    automatic_eod.run_52_week_shadow_scan(
        measurement_date=(
            MEASUREMENT_DATE
        ),
    )

    assert (
        observed["scan_date"]
        == MEASUREMENT_DATE
    )

    assert (
        observed["save_date"]
        == MEASUREMENT_DATE
    )


def test_mean_reversion_eod_wrapper_passes_measurement_date(
    monkeypatch,
):
    observed = {}

    monkeypatch.setattr(
        automatic_eod,
        "load_all_watchlists",
        lambda: ["TEST.TO"],
    )

    def fake_scan(
        watchlist,
        measurement_date=None,
    ):
        observed["scan_date"] = (
            measurement_date
        )

        return {
            "ready": [],
            "watch": [],
            "ignore": [],
            "errors": [],
        }

    def fake_save(
        results,
        measurement_date=None,
    ):
        observed["save_date"] = (
            measurement_date
        )

        return "report.csv"

    monkeypatch.setattr(
        automatic_eod,
        "scan_mean_reversion",
        fake_scan,
    )

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_results",
        fake_save,
    )

    automatic_eod.run_mean_reversion_shadow_scan(
        measurement_date=(
            MEASUREMENT_DATE
        ),
    )

    assert (
        observed["scan_date"]
        == MEASUREMENT_DATE
    )

    assert (
        observed["save_date"]
        == MEASUREMENT_DATE
    )
