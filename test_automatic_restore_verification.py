from datetime import datetime

from paper_trading.automatic_eod import (
    run_restore_verification_after_backup,
)


def test_local_backup_does_not_run_restore():
    called = {
        "value": False
    }

    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        called["value"] = True

        return {
            "success": True,
        }

    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type": "LOCAL",
                "backup_path":
                    r"C:\Northstar_Backups\2026-08-25",
            },
            runner=runner,
        )
    )

    assert result["success"] is True

    assert (
        result["status"]
        == "NOT_APPLICABLE"
    )

    assert result["ran"] is False
    assert called["value"] is False


def test_local_fallback_does_not_run_restore():
    called = {
        "value": False
    }

    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        called["value"] = True

        return {
            "success": True,
        }

    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type":
                    "LOCAL_FALLBACK",
                "backup_path":
                    r"C:\Northstar_Backups\2026-08-25",
            },
            runner=runner,
        )
    )

    assert (
        result["status"]
        == "NOT_APPLICABLE"
    )

    assert called["value"] is False


def test_failed_external_backup_does_not_restore():
    called = {
        "value": False
    }

    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        called["value"] = True

        return {
            "success": True,
        }

    result = (
        run_restore_verification_after_backup(
            {
                "success": False,
                "backup_type":
                    "EXTERNAL",
                "backup_path":
                    r"D:\Northstar_Backups\2026-08-25",
            },
            runner=runner,
        )
    )

    assert (
        result["status"]
        == "NOT_APPLICABLE"
    )

    assert called["value"] is False


def test_external_backup_calls_monthly_runner():
    called = {
        "path": None,
        "datetime": None,
    }

    current_datetime = datetime(
        2026,
        8,
        25,
        16,
        10,
    )

    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        called["path"] = backup_path

        called[
            "datetime"
        ] = current_datetime

        return {
            "success": True,
            "status": "NOT_DUE",
            "ran": False,
            "errors": [],
        }

    backup_path = (
        r"D:\Northstar_Backups\2026-08-25"
    )

    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type":
                    "EXTERNAL",
                "backup_path":
                    backup_path,
            },
            current_datetime=(
                current_datetime
            ),
            runner=runner,
        )
    )

    assert (
        result["status"]
        == "NOT_DUE"
    )

    assert (
        called["path"]
        == backup_path
    )

    assert (
        called["datetime"]
        == current_datetime
    )


def test_due_external_restore_passes():
    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        return {
            "success": True,
            "status": "PASS",
            "ran": True,
            "backup_path":
                backup_path,
            "checked": 12,
            "errors": [],
        }

    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type":
                    "EXTERNAL",
                "backup_path":
                    r"D:\Northstar_Backups\2026-08-25",
            },
            runner=runner,
        )
    )

    assert result["success"] is True
    assert result["status"] == "PASS"
    assert result["ran"] is True
    assert result["checked"] == 12


def test_restore_runner_failure_is_contained():
    def runner(
        backup_path=None,
        current_datetime=None,
    ):
        raise RuntimeError(
            "simulated restore failure"
        )

    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type":
                    "EXTERNAL",
                "backup_path":
                    r"D:\Northstar_Backups\2026-08-25",
            },
            runner=runner,
        )
    )

    assert result["success"] is False
    assert result["status"] == "ERROR"

    assert any(
        "simulated restore failure"
        in error
        for error in result["errors"]
    )


def test_external_backup_without_path_fails_safely():
    result = (
        run_restore_verification_after_backup(
            {
                "success": True,
                "backup_type":
                    "EXTERNAL",
                "backup_path": None,
            }
        )
    )

    assert result["success"] is False
    assert result["status"] == "ERROR"
    assert result["ran"] is False
