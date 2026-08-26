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


def test_cloud_backup_uses_real_execution_time():
    called = {
        "created_at": "NOT_CALLED"
    }

    historical_eod = datetime(
        2026,
        8,
        7,
        16,
        5,
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
            current_datetime=historical_eod,
            runner=runner,
        )
    )

    assert result["success"] is True
    assert result["ran"] is True

    # Critical regression check:
    # historical EOD time must NOT be forwarded
    # to the physical cloud-backup timestamp.
    assert called["created_at"] is None


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
