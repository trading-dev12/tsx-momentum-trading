import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)

from utilities.backup_manager import (
    PROJECT_ROOT,
    load_local_backup_settings,
    resolve_backup_root,
)


CLOUD_KEY_FILE = (
    PROJECT_ROOT
    / "config"
    / "cloud_backup.key"
)

CLOUD_STATUS_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "cloud_backup_status.json"
)

CLOUD_RETENTION_COUNT = 90

CRITICAL_BACKUP_ITEMS = [
    "automatic_eod_state.json",
    "paper_signal_journal.csv",

    "paper_trade_journal.csv",
    "paper_trade_journal_52week.csv",
    "paper_trade_journal_mean_reversion.csv",

    "paper_portfolio_state.json",
    "paper_portfolio_state_52week.json",
    "paper_portfolio_state_mean_reversion.json",

    "pending_trades.csv",
    "pending_trades_52week.csv",
    "pending_trades_mean_reversion.csv",

    "research",
    "validation_reports",
]


def _sha256_bytes(data):
    return hashlib.sha256(
        data
    ).hexdigest()


def _load_key():
    if not CLOUD_KEY_FILE.is_file():
        raise FileNotFoundError(
            "Cloud backup encryption key "
            "is missing."
        )

    key = CLOUD_KEY_FILE.read_bytes()

    # Fernet validates key format here.
    Fernet(key)

    return key


def _cloud_root():
    settings = (
        load_local_backup_settings()
    )

    value = settings.get(
        "cloud_backup_root"
    )

    if not value:
        raise RuntimeError(
            "cloud_backup_root is not "
            "configured in local_settings.json"
        )

    return resolve_backup_root(
        value
    )


def _iter_files():
    for relative_item in (
        CRITICAL_BACKUP_ITEMS
    ):
        source = (
            PROJECT_ROOT
            / relative_item
        )

        if not source.exists():
            continue

        if source.is_file():
            yield (
                relative_item,
                source,
            )

            continue

        for child in sorted(
            source.rglob("*")
        ):
            if not child.is_file():
                continue

            if (
                "__pycache__"
                in child.parts
            ):
                continue

            if child.suffix in (
                ".pyc",
                ".lock",
            ):
                continue

            relative = child.relative_to(
                PROJECT_ROOT
            )

            yield (
                relative.as_posix(),
                child,
            )


def build_encrypted_cloud_archive(
    created_at=None,
):
    """
    Build an authenticated encrypted Northstar
    recovery archive entirely in memory.

    The decrypted ZIP contains a SHA-256 manifest
    covering every included data file.
    """

    if created_at is None:
        created_at = (
            datetime.now()
            .astimezone()
        )

    manifest_files = []
    source_files = []

    for relative, source in _iter_files():
        data = source.read_bytes()

        manifest_files.append(
            {
                "path": relative,
                "size": len(data),
                "sha256":
                    _sha256_bytes(data),
            }
        )

        source_files.append(
            (
                relative,
                data,
            )
        )

    if not source_files:
        raise RuntimeError(
            "No critical Northstar files "
            "were available for cloud backup."
        )

    manifest = {
        "format":
            "NORTHSTAR_CRITICAL_BACKUP",
        "version": 1,
        "created_at":
            created_at.isoformat(),
        "file_count":
            len(source_files),
        "files":
            manifest_files,
    }

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        mode="w",
        compression=(
            zipfile.ZIP_DEFLATED
        ),
        compresslevel=6,
    ) as archive:

        for relative, data in (
            source_files
        ):
            archive.writestr(
                relative,
                data,
            )

        archive.writestr(
            "northstar_manifest.json",
            json.dumps(
                manifest,
                indent=2,
            ).encode("utf-8"),
        )

    plaintext_zip = (
        buffer.getvalue()
    )

    encrypted = Fernet(
        _load_key()
    ).encrypt(
        plaintext_zip
    )

    return {
        "encrypted_bytes":
            encrypted,
        "plaintext_size":
            len(plaintext_zip),
        "encrypted_size":
            len(encrypted),
        "file_count":
            len(source_files),
        "manifest":
            manifest,
        "encrypted_sha256":
            _sha256_bytes(
                encrypted
            ),
    }


def verify_encrypted_cloud_archive(
    archive_path,
):
    """
    Decrypt the archive and verify every file
    against the encrypted manifest.
    """

    archive_path = Path(
        archive_path
    )

    try:
        encrypted = (
            archive_path
            .read_bytes()
        )

        plaintext = Fernet(
            _load_key()
        ).decrypt(
            encrypted
        )

    except (
        OSError,
        InvalidToken,
        ValueError,
    ) as exc:
        return {
            "success": False,
            "checked": 0,
            "errors": [
                (
                    "Unable to decrypt cloud "
                    f"archive: {exc}"
                )
            ],
        }

    errors = []
    checked = 0

    try:
        with zipfile.ZipFile(
            io.BytesIO(
                plaintext
            ),
            mode="r",
        ) as archive:

            manifest = json.loads(
                archive.read(
                    "northstar_manifest.json"
                )
            )

            for record in (
                manifest.get(
                    "files",
                    []
                )
            ):
                relative = record[
                    "path"
                ]

                try:
                    data = archive.read(
                        relative
                    )
                except KeyError:
                    errors.append(
                        f"{relative}: missing "
                        "from decrypted archive"
                    )
                    continue

                checked += 1

                if (
                    len(data)
                    != record["size"]
                ):
                    errors.append(
                        f"{relative}: size "
                        "mismatch"
                    )

                digest = (
                    _sha256_bytes(
                        data
                    )
                )

                if (
                    digest
                    != record["sha256"]
                ):
                    errors.append(
                        f"{relative}: SHA-256 "
                        "mismatch"
                    )

    except (
        OSError,
        zipfile.BadZipFile,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        errors.append(
            (
                "Decrypted archive structure "
                f"is invalid: {exc}"
            )
        )

    return {
        "success":
            len(errors) == 0,
        "checked":
            checked,
        "errors":
            errors,
    }


def load_cloud_backup_status():
    if not CLOUD_STATUS_FILE.exists():
        return {}

    try:
        result = json.loads(
            CLOUD_STATUS_FILE.read_text(
                encoding="utf-8-sig"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(
        result,
        dict,
    ):
        return {}

    return result


def save_cloud_backup_status(
    status,
):
    CLOUD_STATUS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        CLOUD_STATUS_FILE
        .with_suffix(".tmp")
    )

    temporary.write_text(
        json.dumps(
            status,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        CLOUD_STATUS_FILE
    )


def enforce_cloud_retention(
    cloud_root,
    keep=CLOUD_RETENTION_COUNT,
):
    cloud_root = Path(
        cloud_root
    )

    archives = sorted(
        cloud_root.glob(
            "northstar_critical_*.nsbackup"
        ),
        key=lambda path:
            path.name,
        reverse=True,
    )

    removed = []

    for old_archive in (
        archives[keep:]
    ):
        old_archive.unlink()

        removed.append(
            str(old_archive)
        )

    return removed


def create_cloud_backup(
    created_at=None,
):
    """
    Create, encrypt, write, and independently
    verify one Northstar cloud recovery archive.
    """

    if created_at is None:
        created_at = (
            datetime.now()
            .astimezone()
        )

    now_iso = (
        created_at.isoformat()
    )

    previous = (
        load_cloud_backup_status()
    )

    cloud_root = _cloud_root()

    try:
        cloud_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        built = (
            build_encrypted_cloud_archive(
                created_at=created_at
            )
        )

        filename = (
            "northstar_critical_"
            + created_at.strftime(
                "%Y-%m-%d_%H%M%S"
            )
            + ".nsbackup"
        )

        destination = (
            cloud_root
            / filename
        )

        temporary = (
            destination
            .with_suffix(
                ".nsbackup.tmp"
            )
        )

        temporary.write_bytes(
            built[
                "encrypted_bytes"
            ]
        )

        temporary.replace(
            destination
        )

        verification = (
            verify_encrypted_cloud_archive(
                destination
            )
        )

        if not verification[
            "success"
        ]:
            raise RuntimeError(
                "Post-write verification "
                "failed: "
                + "; ".join(
                    verification[
                        "errors"
                    ]
                )
            )

        removed = (
            enforce_cloud_retention(
                cloud_root
            )
        )

        result = {
            "success": True,
            "status": "PASS",
            "backup_path":
                str(destination),
            "file_count":
                built["file_count"],
            "checked":
                verification[
                    "checked"
                ],
            "plaintext_size":
                built[
                    "plaintext_size"
                ],
            "encrypted_size":
                built[
                    "encrypted_size"
                ],
            "encrypted_sha256":
                built[
                    "encrypted_sha256"
                ],
            "retention_removed":
                len(removed),
            "errors": [],
        }

    except Exception as exc:
        result = {
            "success": False,
            "status": "FAIL",
            "backup_path": None,
            "file_count": 0,
            "checked": 0,
            "plaintext_size": 0,
            "encrypted_size": 0,
            "encrypted_sha256": None,
            "retention_removed": 0,
            "errors": [
                str(exc)
            ],
        }

    status = {
        "last_attempt":
            now_iso,
        "last_success":
            previous.get(
                "last_success"
            ),
        "last_backup_success":
            bool(
                result[
                    "success"
                ]
            ),
        "last_backup_path":
            result.get(
                "backup_path"
            ),
        "file_count":
            result.get(
                "file_count",
                0,
            ),
        "checked":
            result.get(
                "checked",
                0,
            ),
        "encrypted_size":
            result.get(
                "encrypted_size",
                0,
            ),
        "encrypted_sha256":
            result.get(
                "encrypted_sha256"
            ),
        "errors":
            result.get(
                "errors",
                [],
            ),
    }

    if result["success"]:
        status[
            "last_success"
        ] = now_iso

    try:
        save_cloud_backup_status(
            status
        )
    except Exception:
        pass

    return result
