from paper_trading.trading_pipeline_validator import (
    ValidationReport,
    validate_eod_state,
)


def get_result(report):
    matches = [
        result
        for result in report.results
        if result.name == "EOD/pending date match"
    ]

    assert len(matches) == 1
    return matches[0]


def test_pending_date_matching_eod_passes():
    report = ValidationReport()

    validate_eod_state(
        {"last_run_date": "2026-08-14"},
        [{"signal_date": "2026-08-14"}],
        report,
    )

    result = get_result(report)

    assert result.status == "PASS"


def test_older_pending_date_is_warning():
    report = ValidationReport()

    validate_eod_state(
        {"last_run_date": "2026-08-14"},
        [{"signal_date": "2026-08-13"}],
        report,
    )

    result = get_result(report)

    assert result.status == "WARNING"
    assert "retained for retry" in result.message


def test_pending_date_newer_than_eod_fails():
    report = ValidationReport()

    validate_eod_state(
        {"last_run_date": "2026-08-14"},
        [{"signal_date": "2026-08-15"}],
        report,
    )

    result = get_result(report)

    assert result.status == "FAIL"
    assert "newer than EOD state" in result.message


def test_invalid_pending_date_fails():
    report = ValidationReport()

    validate_eod_state(
        {"last_run_date": "2026-08-14"},
        [{"signal_date": "not-a-date"}],
        report,
    )

    result = get_result(report)

    assert result.status == "FAIL"
    assert "invalid pending dates" in result.message
