import json
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"

BACKUP_ITEMS = [
    "paper_trade_journal.csv",
    "paper_portfolio_state.json",
    "automatic_eod_state.json",
    "research",
    "validation_reports",
    "data",
]


def load_backup_settings():
    """
    Load backup settings from config/settings.json.
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
            encoding="utf-8",
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


def resolve_backup_root(backup_root_value):
    """
    Convert the configured backup location into an absolute path.
    """

    backup_root = Path(backup_root_value).expanduser()

    if not backup_root.is_absolute():
        backup_root = PROJECT_ROOT / backup_root

    return backup_root


def create_backup(backup_root=None):
    """
    Create a dated backup of important runtime and research data.

    Returns a summary dictionary containing:
    - success
    - enabled
    - backup_path
    - copied
    - skipped
    - errors
    """

    settings = load_backup_settings()

    if not settings["backup_after_eod"]:
        return {
            "success": True,
            "enabled": False,
            "backup_path": "",
            "copied": 0,
            "skipped": 0,
            "errors": [],
        }

    backup_root_value = (
        backup_root
        if backup_root is not None
        else settings["backup_root"]
    )

    backup_root_path = resolve_backup_root(
        backup_root_value,
    )

    today = datetime.now().strftime("%Y-%m-%d")
    destination = backup_root_path / today

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

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
                    shutil.rmtree(target)

                shutil.copytree(
                    source,
                    target,
                    ignore=shutil.ignore_patterns(
                        "__pycache__",
                        "*.pyc",
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
        "enabled": True,
        "backup_path": str(destination),
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
    }