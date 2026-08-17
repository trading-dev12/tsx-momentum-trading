"""
Northstar Quant
Entry-Time Research Context

Preserves the portfolio, sizing and runtime configuration that
existed immediately before a paper position was opened.

Research only. This module never changes sizing, eligibility,
stops, targets, execution or strategy rules.
"""

import hashlib
import json
from pathlib import Path
import subprocess


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

CONFIG_FILES = [
    PROJECT_ROOT
    / "config"
    / "settings.json",

    PROJECT_ROOT
    / "config"
    / "research_validation.json",
]


def _safe_float(
    value,
    default=0.0,
):
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def _hash_files(paths):
    """
    Produce one deterministic SHA256 over filenames + contents.
    """

    digest = hashlib.sha256()
    files_hashed = 0

    unique_paths = sorted(
        {
            Path(path)
            for path in paths
            if Path(path).exists()
        },
        key=lambda path: (
            path.as_posix()
        ),
    )

    for path in unique_paths:
        try:
            relative_path = (
                path.relative_to(
                    PROJECT_ROOT
                )
                .as_posix()
            )
        except ValueError:
            relative_path = (
                path.as_posix()
            )

        digest.update(
            relative_path.encode(
                "utf-8"
            )
        )

        digest.update(b"\0")

        digest.update(
            path.read_bytes()
        )

        digest.update(b"\0")

        files_hashed += 1

    return (
        digest.hexdigest()
        if files_hashed
        else ""
    )


def build_config_snapshot():
    """
    Preserve the non-secret Northstar validation configuration.
    """

    snapshot = {}
    errors = []

    for path in CONFIG_FILES:
        relative_path = (
            path.relative_to(
                PROJECT_ROOT
            )
            .as_posix()
        )

        try:
            snapshot[
                relative_path
            ] = json.loads(
                path.read_text(
                    encoding="utf-8-sig"
                )
            )

        except Exception as error:
            errors.append(
                f"{relative_path}: {error}"
            )

    snapshot_json = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    return (
        snapshot,
        snapshot_json,
        errors,
    )


def get_strategy_code_paths():
    """
    Return code that can materially influence strategy signals.
    """

    paths = []

    for folder_name in (
        "rules",
        "scanner",
        "strategies",
    ):
        folder = (
            PROJECT_ROOT
            / folder_name
        )

        if folder.exists():
            paths.extend(
                folder.rglob(
                    "*.py"
                )
            )

    explicit_paths = [
        PROJECT_ROOT
        / "core"
        / "eod_signal_service.py",

        PROJECT_ROOT
        / "core"
        / "market_data.py",

        PROJECT_ROOT
        / "backtesting"
        / "strategy.py",
    ]

    paths.extend(
        explicit_paths
    )

    return paths


def get_git_commit():
    """
    Return the exact checked-out Git commit when available.
    """

    try:
        result = subprocess.run(
            [
                "git",
                "rev-parse",
                "HEAD",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )

        return (
            result.stdout.strip()
        )

    except Exception:
        return ""


def build_runtime_fingerprint():
    """
    Build code/config identity for later validation research.

    The strategy code hash detects local strategy-code changes
    even when runtime journal files make the worktree dirty.
    """

    (
        config_snapshot,
        config_snapshot_json,
        config_errors,
    ) = build_config_snapshot()

    config_sha256 = _hash_files(
        CONFIG_FILES
    )

    strategy_code_sha256 = (
        _hash_files(
            get_strategy_code_paths()
        )
    )

    git_commit = get_git_commit()

    settings = config_snapshot.get(
        "config/settings.json",
        {},
    )

    errors = list(
        config_errors
    )

    if not git_commit:
        errors.append(
            "Git commit unavailable"
        )

    if not config_sha256:
        errors.append(
            "Config fingerprint unavailable"
        )

    if not strategy_code_sha256:
        errors.append(
            "Strategy code fingerprint unavailable"
        )

    return {
        "entry_git_commit": git_commit,
        "entry_project_version": (
            settings.get(
                "version",
                "",
            )
        ),
        "entry_config_sha256": (
            config_sha256
        ),
        "entry_strategy_code_sha256": (
            strategy_code_sha256
        ),
        "entry_config_snapshot_json": (
            config_snapshot_json
        ),
        "entry_fingerprint_status": (
            "AVAILABLE"
            if not errors
            else "PARTIAL"
        ),
        "entry_fingerprint_error": (
            "; ".join(errors)
        ),
    }


def build_entry_context(
    portfolio,
    sizing_diagnostics,
    entry_price,
    stop_price,
    target_price,
    shares,
    atr_multiplier,
    reward_multiplier,
    max_hold_days,
    signal_close=None,
):
    """
    Capture the exact paper-trading environment before entry.
    """

    summary = portfolio.summary()

    entry_price = _safe_float(
        entry_price
    )

    stop_price = _safe_float(
        stop_price
    )

    target_price = _safe_float(
        target_price
    )

    shares = int(
        shares
    )

    risk_per_share = max(
        entry_price - stop_price,
        0.0,
    )

    initial_risk_amount = (
        risk_per_share
        * shares
    )

    position_value = (
        entry_price
        * shares
    )

    signal_close_value = (
        _safe_float(
            signal_close,
            default=0.0,
        )
    )

    signal_to_entry_gap_percent = (
        (
            (
                entry_price
                - signal_close_value
            )
            / signal_close_value
        )
        * 100
        if signal_close_value > 0
        else 0.0
    )

    context = {
        "entry_context_status": "AVAILABLE",

        "entry_cash_before": (
            summary.get(
                "cash",
                0,
            )
        ),

        "entry_portfolio_value_before": (
            summary.get(
                "portfolio_value",
                0,
            )
        ),

        "entry_open_position_value_before": (
            summary.get(
                "open_position_value",
                0,
            )
        ),

        "entry_portfolio_exposure_before": (
            summary.get(
                "portfolio_exposure",
                0,
            )
        ),

        "entry_open_positions_before": (
            summary.get(
                "open_positions",
                0,
            )
        ),

        "entry_closed_trades_before": (
            summary.get(
                "closed_trades",
                0,
            )
        ),

        "entry_position_value": (
            position_value
        ),

        "entry_initial_risk_per_share": (
            risk_per_share
        ),

        "entry_initial_risk_amount": (
            initial_risk_amount
        ),

        "entry_risk_model": (
            sizing_diagnostics.get(
                "risk_model",
                "",
            )
        ),

        "entry_risk_budget": (
            sizing_diagnostics.get(
                "risk_budget",
                "",
            )
        ),

        "entry_max_position_value": (
            sizing_diagnostics.get(
                "maximum_position_value",
                "",
            )
        ),

        "entry_sizing_limiting_factor": (
            sizing_diagnostics.get(
                "limiting_factor",
                "",
            )
        ),

        "entry_sizing_decision": (
            sizing_diagnostics.get(
                "decision",
                "",
            )
        ),

        "entry_atr_multiplier": (
            atr_multiplier
        ),

        "entry_reward_multiplier": (
            reward_multiplier
        ),

        "entry_max_hold_days": (
            max_hold_days
        ),

        "signal_to_entry_gap_percent": round(
            signal_to_entry_gap_percent,
            6,
        ),
    }

    context.update(
        build_runtime_fingerprint()
    )

    return context
