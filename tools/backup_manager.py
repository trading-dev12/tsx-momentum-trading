"""
Northstar Quant backup manager.

Creates timestamped, verified backups outside the project folder.
The script never modifies files inside the working repository.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_ROOT = Path(r"C:\Northstar_Backups")

BACKUP_ITEMS = [
    "paper_portfolio_state.json",
    "paper_trade_journal.csv",
    "pending_trades.csv",
    "automatic_eod_state.json",
    "data",
    "research",
    "validation_reports",
    "docs",
    "config",
    "watchlists",
    "mobile_dashboard",
    "paper_trading",
    "scanner",
    "strategies",
    "core",
    "gui",
    "tools",
]

REQUIRED_ITEMS = [
    "paper_portfolio_state.json",
    "paper_trade_journal.csv",
    "automatic_eod_state.json",
    "data",
    "research",
]


def copy_item(source: Path, destination: Path) -> None:
    """Copy one file or directory into the backup folder."""
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def verify_backup(backup_folder: Path) -> tuple[bool, list[str]]:
    """Confirm required backup items exist."""
    missing_items: list[str] = []

    for item_name in REQUIRED_ITEMS:
        if not (backup_folder / item_name).exists():
            missing_items.append(item_name)

    return len(missing_items) == 0, missing_items


def write_backup_status(
    backup_folder: Path,
    status: str,
    copied_items: list[str],
    skipped_items: list[str],
    missing_required_items: list[str],
    error_message: str = "",
) -> None:
    """Write machine-readable backup status information."""
    status_data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "backup_folder": str(backup_folder),
        "copied_items": copied_items,
        "skipped_items": skipped_items,
        "missing_required_items": missing_required_items,
        "error_message": error_message,
    }

    status_file = BACKUP_ROOT / "latest_backup_status.json"
    status_file.write_text(
        json.dumps(status_data, indent=4),
        encoding="utf-8",
    )


def create_backup() -> int:
    """Create and verify a timestamped Northstar Quant backup."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_folder = BACKUP_ROOT / timestamp

    copied_items: list[str] = []
    skipped_items: list[str] = []

    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
        backup_folder.mkdir(parents=True, exist_ok=False)

        print("Northstar Quant Backup Manager")
        print(f"Project: {PROJECT_ROOT}")
        print(f"Backup:  {backup_folder}")
        print()

        for item_name in BACKUP_ITEMS:
            source = PROJECT_ROOT / item_name
            destination = backup_folder / item_name

            if not source.exists():
                skipped_items.append(item_name)
                print(f"SKIP  {item_name} (not found)")
                continue

            copy_item(source, destination)
            copied_items.append(item_name)
            print(f"COPY  {item_name}")

        verified, missing_required_items = verify_backup(backup_folder)

        if not verified:
            write_backup_status(
                backup_folder=backup_folder,
                status="FAIL",
                copied_items=copied_items,
                skipped_items=skipped_items,
                missing_required_items=missing_required_items,
            )

            print()
            print("BACKUP FAILED")
            print(
                "Missing required items: "
                + ", ".join(missing_required_items)
            )
            return 1

        backup_summary = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "project_root": str(PROJECT_ROOT),
            "backup_folder": str(backup_folder),
            "copied_items": copied_items,
            "skipped_items": skipped_items,
            "verification": "PASS",
        }

        (backup_folder / "backup_summary.json").write_text(
            json.dumps(backup_summary, indent=4),
            encoding="utf-8",
        )

        write_backup_status(
            backup_folder=backup_folder,
            status="PASS",
            copied_items=copied_items,
            skipped_items=skipped_items,
            missing_required_items=[],
        )

        print()
        print("BACKUP PASSED")
        print(f"Copied items: {len(copied_items)}")
        print(f"Skipped items: {len(skipped_items)}")
        print(f"Saved to: {backup_folder}")

        return 0

    except Exception as error:
        write_backup_status(
            backup_folder=backup_folder,
            status="FAIL",
            copied_items=copied_items,
            skipped_items=skipped_items,
            missing_required_items=[],
            error_message=str(error),
        )

        print()
        print("BACKUP FAILED")
        print(str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(create_backup())