import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

from cryptography.fernet import Fernet

import utilities.cloud_backup as cloud_backup


def configure_test_environment(
    monkeypatch,
    tmp_path,
):
    project_root = (
        tmp_path
        / "northstar"
    )

    project_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    key_file = (
        project_root
        / "config"
        / "cloud_backup.key"
    )

    key_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    key_file.write_bytes(
        Fernet.generate_key()
    )

    status_file = (
        project_root
        / "data"
        / "runtime"
        / "cloud_backup_status.json"
    )

    cloud_root = (
        tmp_path
        / "fake_cloud"
    )

    monkeypatch.setattr(
        cloud_backup,
        "PROJECT_ROOT",
        project_root,
    )

    monkeypatch.setattr(
        cloud_backup,
        "CLOUD_KEY_FILE",
        key_file,
    )

    monkeypatch.setattr(
        cloud_backup,
        "CLOUD_STATUS_FILE",
        status_file,
    )

    monkeypatch.setattr(
        cloud_backup,
        "_cloud_root",
        lambda: cloud_root,
    )

    monkeypatch.setattr(
        cloud_backup,
        "CRITICAL_BACKUP_ITEMS",
        [
            "paper_trade_journal.csv",
            "paper_portfolio_state.json",
            "research",
        ],
    )

    (
        project_root
        / "paper_trade_journal.csv"
    ).write_text(
        "symbol,pnl\nENB.TO,42.50\n",
        encoding="utf-8",
    )

    (
        project_root
        / "paper_portfolio_state.json"
    ).write_text(
        json.dumps(
            {
                "cash": 500000,
                "positions": [],
            }
        ),
        encoding="utf-8",
    )

    research = (
        project_root
        / "research"
    )

    research.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        research
        / "evidence.json"
    ).write_text(
        json.dumps(
            {
                "status": "test"
            }
        ),
        encoding="utf-8",
    )

    return {
        "project_root":
            project_root,
        "key_file":
            key_file,
        "status_file":
            status_file,
        "cloud_root":
            cloud_root,
    }


def test_build_and_verify_encrypted_archive(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    built = (
        cloud_backup
        .build_encrypted_cloud_archive()
    )

    archive_path = (
        environment["cloud_root"]
        / "test.nsbackup"
    )

    archive_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_path.write_bytes(
        built["encrypted_bytes"]
    )

    result = (
        cloud_backup
        .verify_encrypted_cloud_archive(
            archive_path
        )
    )

    assert result["success"] is True

    assert (
        result["checked"]
        == built["file_count"]
    )

    assert result["errors"] == []


def test_ciphertext_corruption_is_detected(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    built = (
        cloud_backup
        .build_encrypted_cloud_archive()
    )

    corrupted = bytearray(
        built["encrypted_bytes"]
    )

    corrupted[
        len(corrupted) // 2
    ] ^= 1

    archive_path = (
        environment["cloud_root"]
        / "corrupt.nsbackup"
    )

    archive_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_path.write_bytes(
        bytes(corrupted)
    )

    result = (
        cloud_backup
        .verify_encrypted_cloud_archive(
            archive_path
        )
    )

    assert result["success"] is False

    assert any(
        "Unable to decrypt"
        in error
        for error in result["errors"]
    )


def test_wrong_key_cannot_decrypt_backup(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    built = (
        cloud_backup
        .build_encrypted_cloud_archive()
    )

    archive_path = (
        environment["cloud_root"]
        / "encrypted.nsbackup"
    )

    archive_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_path.write_bytes(
        built["encrypted_bytes"]
    )

    environment[
        "key_file"
    ].write_bytes(
        Fernet.generate_key()
    )

    result = (
        cloud_backup
        .verify_encrypted_cloud_archive(
            archive_path
        )
    )

    assert result["success"] is False


def test_manifest_hash_mismatch_is_detected(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    key = (
        environment[
            "key_file"
        ].read_bytes()
    )

    original = b"original data"

    manifest = {
        "format":
            "NORTHSTAR_CRITICAL_BACKUP",
        "version": 1,
        "files": [
            {
                "path":
                    "paper_trade_journal.csv",
                "size":
                    len(original),
                "sha256":
                    cloud_backup
                    ._sha256_bytes(
                        original
                    ),
            }
        ],
    }

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "paper_trade_journal.csv",
            b"tampered data",
        )

        archive.writestr(
            "northstar_manifest.json",
            json.dumps(
                manifest
            ),
        )

    encrypted = Fernet(
        key
    ).encrypt(
        buffer.getvalue()
    )

    archive_path = (
        environment["cloud_root"]
        / "manifest_mismatch.nsbackup"
    )

    archive_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archive_path.write_bytes(
        encrypted
    )

    result = (
        cloud_backup
        .verify_encrypted_cloud_archive(
            archive_path
        )
    )

    assert result["success"] is False

    assert any(
        (
            "size mismatch" in error
            or
            "SHA-256 mismatch" in error
        )
        for error in result["errors"]
    )


def test_retention_keeps_newest_archives(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    cloud_root = (
        environment["cloud_root"]
    )

    cloud_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    for index in range(5):
        (
            cloud_root
            / (
                "northstar_critical_"
                f"2026-08-{index + 1:02d}_"
                "160500.nsbackup"
            )
        ).write_bytes(
            b"test"
        )

    removed = (
        cloud_backup
        .enforce_cloud_retention(
            cloud_root,
            keep=3,
        )
    )

    remaining = list(
        cloud_root.glob(
            "northstar_critical_*.nsbackup"
        )
    )

    assert len(removed) == 2
    assert len(remaining) == 3

    names = sorted(
        path.name
        for path in remaining
    )

    assert (
        "northstar_critical_"
        "2026-08-05_160500.nsbackup"
        in names
    )

    assert (
        "northstar_critical_"
        "2026-08-04_160500.nsbackup"
        in names
    )

    assert (
        "northstar_critical_"
        "2026-08-03_160500.nsbackup"
        in names
    )


def test_create_cloud_backup_end_to_end(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    created_at = datetime(
        2026,
        8,
        25,
        16,
        10,
    ).astimezone()

    result = (
        cloud_backup
        .create_cloud_backup(
            created_at=created_at
        )
    )

    assert result["success"] is True
    assert result["status"] == "PASS"

    archive_path = Path(
        result["backup_path"]
    )

    assert archive_path.is_file()

    verify_result = (
        cloud_backup
        .verify_encrypted_cloud_archive(
            archive_path
        )
    )

    assert (
        verify_result["success"]
        is True
    )

    assert (
        environment[
            "status_file"
        ].exists()
    )

    status = json.loads(
        environment[
            "status_file"
        ].read_text(
            encoding="utf-8"
        )
    )

    assert (
        status[
            "last_backup_success"
        ]
        is True
    )

    assert status["last_success"]


def test_missing_encryption_key_fails_safely(
    monkeypatch,
    tmp_path,
):
    environment = (
        configure_test_environment(
            monkeypatch,
            tmp_path,
        )
    )

    environment[
        "key_file"
    ].unlink()

    result = (
        cloud_backup
        .create_cloud_backup()
    )

    assert result["success"] is False
    assert result["status"] == "FAIL"

    assert any(
        "encryption key is missing"
        in error.lower()
        for error in result["errors"]
    )
