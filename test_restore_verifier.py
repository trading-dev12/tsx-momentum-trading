from datetime import datetime

import json

import utilities.restore_verifier as restore_verifier


def make_valid_backup(root):
    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for relative_path in (
        restore_verifier.REQUIRED_CSV_FILES
    ):
        path = root / relative_path

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            "column\nvalue\n",
            encoding="utf-8",
        )

    for relative_path in (
        restore_verifier.REQUIRED_JSON_FILES
    ):
        path = root / relative_path

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            "{}",
            encoding="utf-8",
        )

    research = root / "research"

    research.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        research
        / "restore_test_evidence.txt"
    ).write_text(
        "Northstar restore test",
        encoding="utf-8",
    )

    return root


def use_temporary_status_file(
    monkeypatch,
    tmp_path,
):
    status_file = (
        tmp_path
        / "runtime"
        / "restore_test_status.json"
    )

    monkeypatch.setattr(
        restore_verifier,
        "RESTORE_TEST_STATUS_FILE",
        status_file,
    )

    return status_file


def test_valid_backup_passes(
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path / "backup"
    )

    result = (
        restore_verifier
        .verify_restored_backup(
            backup
        )
    )

    expected_checks = (
        len(
            restore_verifier
            .REQUIRED_CSV_FILES
        )
        + len(
            restore_verifier
            .REQUIRED_JSON_FILES
        )
        + len(
            restore_verifier
            .REQUIRED_DIRECTORIES
        )
    )

    assert result["success"] is True
    assert result["errors"] == []

    assert (
        result["checked"]
        == expected_checks
    )


def test_corrupt_json_fails(
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path / "backup"
    )

    corrupt_file = (
        backup
        / restore_verifier
        .REQUIRED_JSON_FILES[0]
    )

    corrupt_file.write_text(
        "{this is not valid json",
        encoding="utf-8",
    )

    result = (
        restore_verifier
        .verify_restored_backup(
            backup
        )
    )

    assert result["success"] is False

    assert any(
        corrupt_file.name
        in error
        for error in result["errors"]
    )


def test_unreadable_csv_fails(
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path / "backup"
    )

    corrupt_file = (
        backup
        / restore_verifier
        .REQUIRED_CSV_FILES[0]
    )

    corrupt_file.write_bytes(
        b"\xff\xfe\x80\x81"
    )

    result = (
        restore_verifier
        .verify_restored_backup(
            backup
        )
    )

    assert result["success"] is False

    assert any(
        corrupt_file.name
        in error
        for error in result["errors"]
    )


def test_missing_required_file_fails(
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path / "backup"
    )

    missing_file = (
        backup
        / restore_verifier
        .REQUIRED_JSON_FILES[0]
    )

    missing_file.unlink()

    result = (
        restore_verifier
        .verify_restored_backup(
            backup
        )
    )

    assert result["success"] is False

    assert any(
        "File is missing"
        in error
        for error in result["errors"]
    )


def test_run_restore_test_records_success(
    monkeypatch,
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path / "backup"
    )

    status_file = (
        use_temporary_status_file(
            monkeypatch,
            tmp_path,
        )
    )

    result = (
        restore_verifier
        .run_restore_test(
            backup
        )
    )

    assert result["success"] is True

    assert (
        result["backup_path"]
        == str(backup)
    )

    assert status_file.exists()

    status = json.loads(
        status_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        status["last_test_success"]
        is True
    )

    assert status["last_success"]
    assert status["errors"] == []


def test_automatic_lookup_uses_recorded_external_backup(
    monkeypatch,
    tmp_path,
):
    backup = make_valid_backup(
        tmp_path
        / "external"
        / "2026-08-25"
    )

    use_temporary_status_file(
        monkeypatch,
        tmp_path,
    )

    monkeypatch.setattr(
        restore_verifier,
        "load_backup_status",
        lambda: {
            "last_external_backup_path":
                str(backup)
        },
    )

    result = (
        restore_verifier
        .run_restore_test()
    )

    assert result["success"] is True

    assert (
        result["backup_path"]
        == str(backup)
    )


def test_no_physical_backup_fails_safely(
    monkeypatch,
    tmp_path,
):
    status_file = (
        use_temporary_status_file(
            monkeypatch,
            tmp_path,
        )
    )

    monkeypatch.setattr(
        restore_verifier,
        "load_backup_status",
        lambda: {},
    )

    monkeypatch.setattr(
        restore_verifier,
        "load_local_backup_settings",
        lambda: {},
    )

    result = (
        restore_verifier
        .run_restore_test()
    )

    assert result["success"] is False

    assert (
        result["checked"]
        == 0
    )

    assert any(
        "No accessible physical backup"
        in error
        for error in result["errors"]
    )

    status = json.loads(
        status_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        status["last_test_success"]
        is False
    )


def test_restore_test_not_due_before_30_days(
    monkeypatch,
    tmp_path,
):
    status_file = (
        use_temporary_status_file(
            monkeypatch,
            tmp_path,
        )
    )

    status_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    status_file.write_text(
        json.dumps(
            {
                "last_success":
                    "2026-08-25T09:35:00-04:00"
            }
        ),
        encoding="utf-8",
    )

    schedule = (
        restore_verifier
        .get_restore_test_schedule(
            datetime(
                2026,
                9,
                20,
                9,
                35,
            )
        )
    )

    assert schedule["due"] is False

    assert (
        schedule["next_due"]
        .date()
        .isoformat()
        == "2026-09-24"
    )


def test_restore_test_due_after_30_days(
    monkeypatch,
    tmp_path,
):
    status_file = (
        use_temporary_status_file(
            monkeypatch,
            tmp_path,
        )
    )

    status_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    status_file.write_text(
        json.dumps(
            {
                "last_success":
                    "2026-08-25T09:35:00-04:00"
            }
        ),
        encoding="utf-8",
    )

    schedule = (
        restore_verifier
        .get_restore_test_schedule(
            datetime(
                2026,
                9,
                24,
                10,
                0,
            )
        )
    )

    assert schedule["due"] is True


def test_if_due_skips_restore_before_deadline(
    monkeypatch,
):
    monkeypatch.setattr(
        restore_verifier,
        "get_restore_test_schedule",
        lambda current_datetime=None: {
            "due": False,
            "next_due":
                datetime(
                    2026,
                    9,
                    24,
                    9,
                    35,
                ),
        },
    )

    called = {
        "value": False
    }

    def fake_restore_test(
        backup_path=None,
    ):
        called["value"] = True

        return {
            "success": True,
        }

    monkeypatch.setattr(
        restore_verifier,
        "run_restore_test",
        fake_restore_test,
    )

    result = (
        restore_verifier
        .run_restore_test_if_due(
            backup_path=
                r"D:\Northstar_Backups\2026-08-25"
        )
    )

    assert result["success"] is True
    assert result["status"] == "NOT_DUE"
    assert result["ran"] is False
    assert called["value"] is False


def test_if_due_runs_restore_test(
    monkeypatch,
):
    monkeypatch.setattr(
        restore_verifier,
        "get_restore_test_schedule",
        lambda current_datetime=None: {
            "due": True,
            "next_due":
                datetime(
                    2026,
                    8,
                    25,
                    9,
                    35,
                ),
        },
    )

    called = {
        "path": None
    }

    def fake_restore_test(
        backup_path=None,
    ):
        called["path"] = backup_path

        return {
            "success": True,
            "backup_path": backup_path,
            "checked": 12,
            "checks": [],
            "errors": [],
        }

    monkeypatch.setattr(
        restore_verifier,
        "run_restore_test",
        fake_restore_test,
    )

    backup_path = (
        r"D:\Northstar_Backups\2026-08-25"
    )

    result = (
        restore_verifier
        .run_restore_test_if_due(
            backup_path=backup_path
        )
    )

    assert result["success"] is True
    assert result["status"] == "PASS"
    assert result["ran"] is True

    assert (
        called["path"]
        == backup_path
    )
