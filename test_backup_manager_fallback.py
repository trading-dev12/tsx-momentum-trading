import json
from pathlib import Path

import utilities.backup_manager as backup_manager


def prepare_backup_test(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()

    sample = project / "sample.txt"
    sample.write_text(
        "northstar evidence",
        encoding="utf-8",
    )

    settings = project / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "backup_root": "Northstar_Backups",
                "backup_after_eod": True,
            }
        ),
        encoding="utf-8",
    )

    local_settings = project / "local_settings.json"

    monkeypatch.setattr(
        backup_manager,
        "PROJECT_ROOT",
        project,
    )

    monkeypatch.setattr(
        backup_manager,
        "SETTINGS_PATH",
        settings,
    )

    monkeypatch.setattr(
        backup_manager,
        "LOCAL_SETTINGS_PATH",
        local_settings,
        raising=False,
    )

    monkeypatch.setattr(
        backup_manager,
        "BACKUP_STATUS_FILE",
        project
        / "data"
        / "runtime"
        / "backup_status.json",
        raising=False,
    )

    monkeypatch.setattr(
        backup_manager,
        "BACKUP_ITEMS",
        ["sample.txt"],
    )

    return project, local_settings


def test_external_backup_is_preferred(
    tmp_path,
    monkeypatch,
):
    project, local_settings = prepare_backup_test(
        tmp_path,
        monkeypatch,
    )

    external = tmp_path / "external"

    local_settings.write_text(
        json.dumps(
            {
                "external_backup_root": str(
                    external
                )
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        backup_manager,
        "external_backup_available",
        lambda path: True,
        raising=False,
    )

    result = backup_manager.create_backup()

    assert result["success"] is True
    assert result["backup_type"] == "EXTERNAL"
    assert result["external_available"] is True

    assert (
        external
        / result["backup_date"]
        / "sample.txt"
    ).exists()


def test_missing_external_drive_uses_local_fallback(
    tmp_path,
    monkeypatch,
):
    project, local_settings = prepare_backup_test(
        tmp_path,
        monkeypatch,
    )

    external = tmp_path / "external"

    local_settings.write_text(
        json.dumps(
            {
                "external_backup_root": str(
                    external
                )
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        backup_manager,
        "external_backup_available",
        lambda path: False,
        raising=False,
    )

    result = backup_manager.create_backup()

    assert result["success"] is True
    assert result["backup_type"] == "LOCAL_FALLBACK"
    assert result["external_available"] is False

    local_root = (
        project / "Northstar_Backups"
    )

    assert (
        local_root
        / result["backup_date"]
        / "sample.txt"
    ).exists()


def test_local_fallback_preserves_last_external_success(
    tmp_path,
    monkeypatch,
):
    project, local_settings = prepare_backup_test(
        tmp_path,
        monkeypatch,
    )

    external = tmp_path / "external"

    local_settings.write_text(
        json.dumps(
            {
                "external_backup_root": str(
                    external
                )
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        backup_manager,
        "external_backup_available",
        lambda path: True,
        raising=False,
    )

    first = backup_manager.create_backup()

    assert first["backup_type"] == "EXTERNAL"

    status_file = (
        project
        / "data"
        / "runtime"
        / "backup_status.json"
    )

    first_status = json.loads(
        status_file.read_text(
            encoding="utf-8"
        )
    )

    external_time = first_status[
        "last_external_success"
    ]

    monkeypatch.setattr(
        backup_manager,
        "external_backup_available",
        lambda path: False,
        raising=False,
    )

    second = backup_manager.create_backup()

    assert second["backup_type"] == "LOCAL_FALLBACK"

    second_status = json.loads(
        status_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        second_status["last_external_success"]
        == external_time
    )
