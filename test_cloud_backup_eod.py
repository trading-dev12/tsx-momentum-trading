from datetime import datetime

from paper_trading.automatic_eod import (
    run_cloud_backup_after_eod,
)


def test_cloud_backup_not_requested_is_safe():
    result = (
        run_cloud_backup_after_eod()
    )

    assert result["success"] is True
    assert result["status"] == "NOT_REQUESTED"
    assert result["ran"] is False


def test_cloud_backup_runs_when_enabled():
    called = {
        "created_at": None
    }

    current_datetime = datetime(
        2026,
        8,
        25,
        16,
        10,
    )

    def runner(
        created_at=None,
    ):
        called["created_at"] = (
            created_at
        )

        return {
            "success": True,
            "status": "PASS",
            "backup_path":
                r"C:\OneDrive\Northstar.nsbackup",
            "file_count": 162,
            "checked": 162,
            "errors": [],
        }

    result = (
        run_cloud_backup_after_eod(
            current_datetime=(
                current_datetime
            ),
            runner=runner,
        )
    )

    assert result["success"] is True
    assert result["status"] == "PASS"
    assert result["ran"] is True

    assert (
        called["created_at"]
        == current_datetime
    )


def test_cloud_failure_is_contained():
    def runner(
        created_at=None,
    ):
        raise RuntimeError(
            "simulated OneDrive failure"
        )

    result = (
        run_cloud_backup_after_eod(
            runner=runner
        )
    )

    assert result["success"] is False
    assert result["status"] == "ERROR"
    assert result["ran"] is True

    assert any(
        "simulated OneDrive failure"
        in error
        for error in result["errors"]
    )


def test_bad_cloud_runner_result_is_contained():
    def runner(
        created_at=None,
    ):
        return None

    result = (
        run_cloud_backup_after_eod(
            runner=runner
        )
    )

    assert result["success"] is False
    assert result["status"] == "ERROR"
    assert result["ran"] is True
