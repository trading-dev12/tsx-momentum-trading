from datetime import datetime

from paper_trading.automatic_eod import run_automatic_eod_cycle


class FakePaperEngine:
    def queue_eod_signals(self, results):
        return {
            "added": len(results["ready"]),
            "rejected": 0,
        }


def fake_scan_provider(current_datetime=None):
    return {
        "ready": [
            {"symbol": "TEST1.TO"},
            {"symbol": "TEST2.TO"},
        ],
        "watch": [
            {"symbol": "WATCH.TO"},
        ],
        "ignore": [],
        "errors": [],
    }


def fake_validation_runner(state_file=None):
    return {
        "success": True,
        "status": "PASS",
        "report_path": "validation_reports/test_report.json",
        "message": "Validation completed successfully.",
    }


summary = run_automatic_eod_cycle(
    paper_engine=FakePaperEngine(),
    current_datetime=datetime(2026, 7, 16, 17, 0),
    state_file="test_automatic_eod_state.json",
    scan_provider=fake_scan_provider,
    validation_runner=fake_validation_runner,
)

print()
print("Validation section:")
print(summary["validation"])

assert summary["status"] == "COMPLETED"
assert summary["ready"] == 2
assert summary["watch"] == 1
assert summary["ignored"] == 0
assert summary["queued"] == 2
assert summary["validation"]["status"] == "PASS"

print()
print("Automatic EOD validation integration test passed.")