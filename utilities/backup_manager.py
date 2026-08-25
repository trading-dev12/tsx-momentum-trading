import json
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"
LOCAL_SETTINGS_PATH = (
    PROJECT_ROOT
    / "config"
    / "local_settings.json"
)
BACKUP_STATUS_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "backup_status.json"
)

BACKUP_ITEMS = [
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
    "data",
]


def load_backup_settings():
    """
    Load portable backup settings from config/settings.json.
    """

    default_settings = {
        "backup_root": "Northstar_Backups",
        "backup_after_eod": True,
    }

    if not SETTINGS_PATH.exists():
        return default_settings

    try:
        with SETTINGS_PATH.open(
            "r",
            encoding="utf-8-sig",
        ) as settings_file:
            settings = json.load(settings_file)

    except (OSError, json.JSONDecodeError):
        return default_settings

    return {
        "backup_root": settings.get(
            "backup_root",
            default_settings["backup_root"],
        ),
        "backup_after_eod": settings.get(
            "backup_after_eod",
            default_settings["backup_after_eod"],
        ),
    }


def load_local_backup_settings():
    """
    Load machine-specific backup settings.

    This file is intentionally excluded from Git so a machine can
    define its own removable/external backup location.
    """

    if not LOCAL_SETTINGS_PATH.exists():
        return {}

    try:
        with LOCAL_SETTINGS_PATH.open(
            "r",
            encoding="utf-8-sig",
        ) as settings_file:
            settings = json.load(settings_file)

    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(settings, dict):
        return {}

    return settings


def resolve_backup_root(backup_root_value):
    """
    Convert a configured backup location into an absolute path.
    """

    backup_root = Path(
        backup_root_value
    ).expanduser()

    if not backup_root.is_absolute():
        backup_root = (
            PROJECT_ROOT
            / backup_root
        )

    return backup_root


def external_backup_available(
    backup_root_path,
):
    """
    Return True when the filesystem containing an external
    backup root is currently available.

    The backup directory itself does not need to exist yet.
    """

    backup_root_path = Path(
        backup_root_path
    )

    anchor = backup_root_path.anchor

    if anchor:
        try:
            return Path(anchor).exists()
        except OSError:
            return False

    try:
        return backup_root_path.parent.exists()
    except OSError:
        return False


def load_backup_status():
    """
    Read the most recently recorded backup status.
    """

    if not BACKUP_STATUS_FILE.exists():
        return {}

    try:
        with BACKUP_STATUS_FILE.open(
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


def save_backup_status(status):
    """
    Persist backup health information for the dashboard.
    """

    BACKUP_STATUS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = (
        BACKUP_STATUS_FILE
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
        BACKUP_STATUS_FILE
    )


def _copy_backup(
    backup_root_path,
    backup_date,
):
    """
    Copy all configured Northstar backup items to one root.
    """

    destination = (
        backup_root_path
        / backup_date
    )

    try:
        destination.mkdir(
            parents=True,
            exist_ok=True,
        )
    except Exception as exc:
        return {
            "success": False,
            "backup_path": str(
                destination
            ),
            "copied": 0,
            "skipped": 0,
            "errors": [
                (
                    "Unable to create backup "
                    f"destination: {exc}"
                )
            ],
        }

    copied = 0
    skipped = 0
    errors = []

    for item in BACKUP_ITEMS:
        source = PROJECT_ROOT / item

        if not source.exists():
            skipped += 1
            continue

        target = destination / item

        try:
            if source.is_dir():
                if target.exists():
                    shutil.rmtree(
                        target
                    )

                shutil.copytree(
                    source,
                    target,
                    ignore=shutil.ignore_patterns(
                        "__pycache__",
                        "*.pyc",
                        "*.lock",
                    ),
                )

            else:
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                shutil.copy2(
                    source,
                    target,
                )

            copied += 1

        except Exception as exc:
            errors.append(
                f"{item}: {exc}"
            )

    return {
        "success": len(errors) == 0,
        "backup_path": str(
            destination
        ),
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
    }


def _record_backup_status(
    result,
    backup_type,
    backup_date,
    external_available,
    external_root=None,
    fallback_reason=None,
):
    """
    Update dashboard-readable backup health state.
    """

    now = datetime.now().astimezone()
    now_iso = now.isoformat()

    previous = load_backup_status()

    status = {
        "last_attempt": now_iso,
        "last_success": previous.get(
            "last_success"
        ),
        "last_backup_type": (
            backup_type
        ),
        "last_backup_path": (
            result.get(
                "backup_path"
            )
        ),
        "last_backup_success": bool(
            result.get(
                "success",
                False,
            )
        ),
        "external_available": bool(
            external_available
        ),
        "external_backup_root": (
            str(external_root)
            if external_root
            else None
        ),
        "last_external_success": (
            previous.get(
                "last_external_success"
            )
        ),
        "last_external_backup_path": (
            previous.get(
                "last_external_backup_path"
            )
        ),
        "last_local_success": (
            previous.get(
                "last_local_success"
            )
        ),
        "last_local_backup_path": (
            previous.get(
                "last_local_backup_path"
            )
        ),
        "fallback_reason": (
            fallback_reason
        ),
    }

    if result.get(
        "success",
        False,
    ):
        status[
            "last_success"
        ] = now_iso

        if backup_type == "EXTERNAL":
            status[
                "last_external_success"
            ] = now_iso
            status[
                "last_external_backup_path"
            ] = result.get(
                "backup_path"
            )

        elif backup_type in (
            "LOCAL",
            "LOCAL_FALLBACK",
        ):
            status[
                "last_local_success"
            ] = now_iso
            status[
                "last_local_backup_path"
            ] = result.get(
                "backup_path"
            )

    try:
        save_backup_status(
            status
        )
    except Exception:
        # Status reporting must never turn a successful
        # evidence backup into a failed backup.
        pass


def create_backup(backup_root=None):
    """
    Create a dated backup of important runtime and research data.

    Normal EOD behavior:
    1. Prefer the configured external backup location when available.
    2. Fall back automatically to the portable local backup location
       when the external drive is unavailable or the external copy fails.
    3. Record backup health for dashboard display.

    An explicit backup_root argument retains manual single-destination
    behavior.

    Returns a summary dictionary containing:
    - success
    - enabled
    - backup_path
    - backup_type
    - backup_date
    - copied
    - skipped
    - errors
    - external_available
    """

    settings = load_backup_settings()

    backup_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    if not settings[
        "backup_after_eod"
    ]:
        return {
            "success": True,
            "enabled": False,
            "backup_path": "",
            "backup_type": "DISABLED",
            "backup_date": backup_date,
            "copied": 0,
            "skipped": 0,
            "errors": [],
            "external_available": False,
        }

    #
    # Explicit/manual destination.
    #
    if backup_root is not None:
        root = resolve_backup_root(
            backup_root
        )

        result = _copy_backup(
            root,
            backup_date,
        )

        result.update(
            {
                "enabled": True,
                "backup_type": "MANUAL",
                "backup_date": backup_date,
                "external_available": (
                    external_backup_available(
                        root
                    )
                ),
            }
        )

        return result

    local_root = resolve_backup_root(
        settings["backup_root"]
    )

    local_settings = (
        load_local_backup_settings()
    )

    external_value = (
        local_settings.get(
            "external_backup_root"
        )
    )

    #
    # No external destination configured:
    # retain original local behavior.
    #
    if not external_value:
        result = _copy_backup(
            local_root,
            backup_date,
        )

        result.update(
            {
                "enabled": True,
                "backup_type": "LOCAL",
                "backup_date": backup_date,
                "external_available": False,
            }
        )

        _record_backup_status(
            result=result,
            backup_type="LOCAL",
            backup_date=backup_date,
            external_available=False,
        )

        return result

    external_root = resolve_backup_root(
        external_value
    )

    external_available = (
        external_backup_available(
            external_root
        )
    )

    #
    # Preferred path: physical/external drive.
    #
    if external_available:
        external_result = (
            _copy_backup(
                external_root,
                backup_date,
            )
        )

        if external_result[
            "success"
        ]:
            external_result.update(
                {
                    "enabled": True,
                    "backup_type": "EXTERNAL",
                    "backup_date": backup_date,
                    "external_available": True,
                }
            )

            _record_backup_status(
                result=external_result,
                backup_type="EXTERNAL",
                backup_date=backup_date,
                external_available=True,
                external_root=external_root,
            )

            return external_result

        fallback_reason = (
            "External backup failed: "
            + "; ".join(
                external_result.get(
                    "errors",
                    [],
                )
            )
        )

    else:
        fallback_reason = (
            "External backup drive "
            "is unavailable."
        )

    #
    # Safety path: local fallback.
    #
    local_result = _copy_backup(
        local_root,
        backup_date,
    )

    local_result.update(
        {
            "enabled": True,
            "backup_type": "LOCAL_FALLBACK",
            "backup_date": backup_date,
            "external_available": (
                external_available
            ),
            "fallback_reason": (
                fallback_reason
            ),
        }
    )

    _record_backup_status(
        result=local_result,
        backup_type="LOCAL_FALLBACK",
        backup_date=backup_date,
        external_available=external_available,
        external_root=external_root,
        fallback_reason=fallback_reason,
    )

    return local_result
