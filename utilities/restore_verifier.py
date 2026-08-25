import csv
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from utilities.backup_manager import (
    PROJECT_ROOT,
    external_backup_available,
    load_backup_status,
    load_local_backup_settings,
    resolve_backup_root,
)


RESTORE_TEST_STATUS_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "restore_test_status.json"
)

RESTORE_TEST_INTERVAL_DAYS = 30


REQUIRED_CSV_FILES = [
    "paper_trade_journal.csv",
    "paper_trade_journal_52week.csv",
    "paper_trade_journal_mean_reversion.csv",

    "pending_trades.csv",
    "pending_trades_52week.csv",
    "pending_trades_mean_reversion.csv",

    "paper_signal_journal.csv",
]

REQUIRED_JSON_FILES = [
    "paper_portfolio_state.json",
    "paper_portfolio_state_52week.json",
    "paper_portfolio_state_mean_reversion.json",
    "automatic_eod_state.json",
]

REQUIRED_DIRECTORIES = [
    "research",
]


def load_restore_test_status():
    if not RESTORE_TEST_STATUS_FILE.exists():
        return {}

    try:
        with RESTORE_TEST_STATUS_FILE.open(
            "r",
            encoding="utf-8-sig",
        ) as status_file:
            status = json.load(
                status_file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(status, dict):
        return {}

    return status


def save_restore_test_status(status):
    RESTORE_TEST_STATUS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = (
        RESTORE_TEST_STATUS_FILE
        .with_suffix(".tmp")
    )

    temporary_file.write_text(
        json.dumps(
            status,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary_file.replace(
        RESTORE_TEST_STATUS_FILE
    )


def _find_latest_external_backup():
    """
    Prefer the exact backup path recorded by the
    backup manager. If that is unavailable, inspect
    the configured external backup root and use its
    newest dated backup directory.
    """

    status = load_backup_status()

    recorded_path = status.get(
        "last_external_backup_path"
    )

    if recorded_path:
        recorded = Path(
            recorded_path
        )

        if recorded.is_dir():
            return recorded

    local_settings = (
        load_local_backup_settings()
    )

    external_value = local_settings.get(
        "external_backup_root"
    )

    if not external_value:
        return None

    external_root = resolve_backup_root(
        external_value
    )

    if not external_backup_available(
        external_root
    ):
        return None

    if not external_root.exists():
        return None

    candidates = []

    for child in external_root.iterdir():
        if not child.is_dir():
            continue

        try:
            datetime.strptime(
                child.name,
                "%Y-%m-%d",
            )
        except ValueError:
            continue

        candidates.append(
            child
        )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda item: item.name,
    )


def _verify_csv(path):
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.reader(
                csv_file
            )

            header = next(
                reader,
                None,
            )

    except (
        OSError,
        csv.Error,
        UnicodeError,
    ) as exc:
        return (
            False,
            str(exc),
        )

    if not header:
        return (
            False,
            "CSV has no header row.",
        )

    return (
        True,
        None,
    )


def _verify_json(path):
    try:
        with path.open(
            "r",
            encoding="utf-8-sig",
        ) as json_file:
            json.load(
                json_file
            )

    except (
        OSError,
        json.JSONDecodeError,
        UnicodeError,
    ) as exc:
        return (
            False,
            str(exc),
        )

    return (
        True,
        None,
    )


def _verify_directory(path):
    if not path.is_dir():
        return (
            False,
            "Directory is missing.",
        )

    try:
        contains_files = any(
            item.is_file()
            for item in path.rglob("*")
        )

    except OSError as exc:
        return (
            False,
            str(exc),
        )

    if not contains_files:
        return (
            False,
            "Directory contains no files.",
        )

    return (
        True,
        None,
    )


def verify_restored_backup(
    restored_root,
):
    restored_root = Path(
        restored_root
    )

    checks = []
    errors = []

    for relative_path in REQUIRED_CSV_FILES:
        path = (
            restored_root
            / relative_path
        )

        if not path.is_file():
            success = False
            error = "File is missing."
        else:
            success, error = (
                _verify_csv(path)
            )

        checks.append(
            {
                "item": relative_path,
                "type": "CSV",
                "success": success,
                "error": error,
            }
        )

        if not success:
            errors.append(
                f"{relative_path}: {error}"
            )

    for relative_path in REQUIRED_JSON_FILES:
        path = (
            restored_root
            / relative_path
        )

        if not path.is_file():
            success = False
            error = "File is missing."
        else:
            success, error = (
                _verify_json(path)
            )

        checks.append(
            {
                "item": relative_path,
                "type": "JSON",
                "success": success,
                "error": error,
            }
        )

        if not success:
            errors.append(
                f"{relative_path}: {error}"
            )

    for relative_path in REQUIRED_DIRECTORIES:
        path = (
            restored_root
            / relative_path
        )

        success, error = (
            _verify_directory(path)
        )

        checks.append(
            {
                "item": relative_path,
                "type": "DIRECTORY",
                "success": success,
                "error": error,
            }
        )

        if not success:
            errors.append(
                f"{relative_path}: {error}"
            )

    return {
        "success": len(errors) == 0,
        "checks": checks,
        "errors": errors,
        "checked": len(checks),
    }


def run_restore_test(
    backup_path=None,
):
    """
    Perform a non-destructive disaster-recovery test.

    The selected physical backup is copied into a
    temporary directory, validated there, and then
    automatically removed.
    """

    now = datetime.now().astimezone()
    now_iso = now.isoformat()

    previous_status = (
        load_restore_test_status()
    )

    if backup_path is None:
        source = (
            _find_latest_external_backup()
        )
    else:
        source = Path(
            backup_path
        )

    if source is None:
        result = {
            "success": False,
            "backup_path": None,
            "checked": 0,
            "checks": [],
            "errors": [
                (
                    "No accessible physical "
                    "backup was found."
                )
            ],
        }

    elif not source.is_dir():
        result = {
            "success": False,
            "backup_path": str(source),
            "checked": 0,
            "checks": [],
            "errors": [
                (
                    "Selected backup path "
                    "does not exist."
                )
            ],
        }

    else:
        try:
            with tempfile.TemporaryDirectory(
                prefix=(
                    "northstar_restore_verify_"
                )
            ) as temporary_directory:

                restored_root = (
                    Path(
                        temporary_directory
                    )
                    / "Northstar_Restore"
                )

                shutil.copytree(
                    source,
                    restored_root,
                )

                result = (
                    verify_restored_backup(
                        restored_root
                    )
                )

                result[
                    "backup_path"
                ] = str(source)

        except Exception as exc:
            result = {
                "success": False,
                "backup_path": str(source),
                "checked": 0,
                "checks": [],
                "errors": [
                    (
                        "Restore copy failed: "
                        f"{exc}"
                    )
                ],
            }

    status = {
        "last_attempt": now_iso,
        "last_success": (
            previous_status.get(
                "last_success"
            )
        ),
        "last_test_success": bool(
            result["success"]
        ),
        "last_test_backup_path": (
            result.get(
                "backup_path"
            )
        ),
        "checked": result.get(
            "checked",
            0,
        ),
        "errors": result.get(
            "errors",
            [],
        ),
    }

    if result["success"]:
        status["last_success"] = (
            now_iso
        )

    try:
        save_restore_test_status(
            status
        )
    except Exception:
        # Reporting failure must not alter
        # the restore-test result.
        pass

    return result


def _parse_status_datetime(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value)
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.astimezone()

    return parsed


def get_restore_test_schedule(
    current_datetime=None,
):
    """
    Return the rolling 30-day restore-test
    schedule based on the most recent
    successful restore verification.
    """

    if current_datetime is None:
        now = datetime.now().astimezone()

    elif current_datetime.tzinfo is None:
        now = (
            current_datetime
            .astimezone()
        )

    else:
        now = current_datetime

    status = load_restore_test_status()

    last_success = (
        _parse_status_datetime(
            status.get(
                "last_success"
            )
        )
    )

    if last_success is None:
        return {
            "now": now,
            "last_success": None,
            "next_due": now,
            "due": True,
            "seconds_until_due": 0,
        }

    next_due = (
        last_success
        + timedelta(
            days=RESTORE_TEST_INTERVAL_DAYS
        )
    )

    seconds_until_due = (
        next_due - now
    ).total_seconds()

    return {
        "now": now,
        "last_success": last_success,
        "next_due": next_due,
        "due": (
            seconds_until_due <= 0
        ),
        "seconds_until_due": (
            seconds_until_due
        ),
    }


def run_restore_test_if_due(
    backup_path=None,
    current_datetime=None,
):
    """
    Run the physical-backup restore verification
    only when the rolling monthly test is due.
    """

    schedule = get_restore_test_schedule(
        current_datetime
    )

    if not schedule["due"]:
        return {
            "success": True,
            "status": "NOT_DUE",
            "ran": False,
            "backup_path": backup_path,
            "next_due": (
                schedule[
                    "next_due"
                ].isoformat()
            ),
            "errors": [],
        }

    result = run_restore_test(
        backup_path=backup_path
    )

    result["ran"] = True

    result["status"] = (
        "PASS"
        if result["success"]
        else "FAIL"
    )

    return result


if __name__ == "__main__":
    result = run_restore_test()

    print(
        "RESTORE TEST:",
        (
            "PASS"
            if result["success"]
            else "FAIL"
        ),
    )

    print(
        "Backup:",
        result.get(
            "backup_path"
        ),
    )

    print(
        "Checks:",
        result.get(
            "checked",
            0,
        ),
    )

    if result.get("errors"):
        print("Errors:")

        for error in result["errors"]:
            print(
                " -",
                error,
            )
