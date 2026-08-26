"""
Automatic End-of-Day Signal Service

Runs the production EOD scanner once per eligible trading day
after the TSX closes, queues READY signals, and records the date
so application refreshes or restarts do not repeat the scan.

The service runs in a background daemon thread so it does not
block the Trading Workstation.
"""

from utilities.backup_manager import create_backup
from utilities.cloud_backup import (
    create_cloud_backup,
)
from utilities.restore_verifier import (
    run_restore_test_if_due,
)
from datetime import datetime, time, timedelta
import json
import os
from pathlib import Path
import threading

from core.eod_signal_service import scan_eod_signals
from core.market_hours import (
    TORONTO_TIMEZONE,
    get_tsx_market_close_time,
    is_tsx_trading_day,
)
from notifications.telegram_notifier import send_telegram_message
from core.watchlist_loader import load_all_watchlists
from scanner.breakout_52week_scanner import (
    save_results as save_52_week_results,
    scan_52_week_breakouts,
)
from scanner.mean_reversion_scanner import (
    save_results as save_mean_reversion_results,
    scan_mean_reversion,
)
from research.market_regime import (
    calculate_market_regime,
)
from research.candidate_history_service import (
    capture_all_candidate_history,
)
from research.momentum_universe_snapshot import (
    save_momentum_universe_snapshot,
)
from research.candidate_forward_outcome_service import (
    run_candidate_forward_outcome_refresh,
)
from research.mean_reversion_guard_research import (
    save_mean_reversion_guard_research,
)
from strategies.mean_reversion_market_guard import (
    build_guarded_mean_reversion_queue_results,
)
from paper_trading.eod_time_exit import (
    run_eod_time_exits,
)
from paper_trading.trading_pipeline_validator import (
    run_validation,
    save_validation_report,
)

from paper_trading.signal_journal import record_ready_signals

from paper_trading.eod_recovery import (
    get_recoverable_eod_datetime,
)

AUTO_EOD_STATE_FILE = "automatic_eod_state.json"
AUTO_EOD_DELAY_MINUTES = 5
DEFAULT_CHECK_SECONDS = 60


def run_forward_outcome_research_capture(
    runner,
    current_date,
):
    """
    Run candidate forward-outcome research without allowing
    research availability to fail the production EOD cycle.
    """

    if runner is None:
        return {
            "success": True,
            "status": "NOT_REQUESTED",
            "as_of_date": str(
                current_date
            ),
        }

    try:
        result = runner(
            as_of_date=current_date,
        )

        if not isinstance(
            result,
            dict,
        ):
            raise TypeError(
                "Forward outcome runner did not "
                "return a result dictionary."
            )

        return result

    except Exception as error:
        return {
            "success": False,
            "status": "ERROR",
            "as_of_date": str(
                current_date
            ),
            "message": str(
                error
            ),
        }


def normalize_current_datetime(current_datetime=None):
    """
    Return a timezone-aware Toronto datetime.
    """

    if current_datetime is None:
        return datetime.now(TORONTO_TIMEZONE)

    if current_datetime.tzinfo is None:
        return current_datetime.replace(
            tzinfo=TORONTO_TIMEZONE,
        )

    return current_datetime.astimezone(
        TORONTO_TIMEZONE,
    )


def get_pending_trade_count(
    paper_engine,
    fallback=0,
):
    """
    Return the current pending-trade count when the engine
    exposes a pending queue.

    Lightweight test doubles may not provide pending_trades,
    so fall back to the supplied count without failing EOD.
    """

    try:
        fallback = max(
            0,
            int(fallback or 0),
        )
    except (TypeError, ValueError):
        fallback = 0

    if paper_engine is None:
        return fallback

    pending_trades = getattr(
        paper_engine,
        "pending_trades",
        None,
    )

    get_all = getattr(
        pending_trades,
        "get_all",
        None,
    )

    if not callable(get_all):
        return fallback

    try:
        return len(get_all())
    except Exception:
        return fallback


def build_pending_execution_footer(
    total_pending,
):
    """Return an accurate EOD pending-execution message."""

    try:
        total_pending = max(
            0,
            int(total_pending or 0),
        )
    except (TypeError, ValueError):
        total_pending = 0

    if total_pending == 0:
        return (
            "No pending signals awaiting "
            "next-day execution."
        )

    if total_pending == 1:
        return (
            "1 pending signal is ready for "
            "next-day execution."
        )

    return (
        f"{total_pending} pending signals are ready "
        "for next-day execution."
    )


def load_last_run_date(
    state_file=AUTO_EOD_STATE_FILE,
):
    """
    Load the last successfully completed automatic EOD date.
    """

    if not os.path.exists(state_file):
        return None

    try:
        with open(
            state_file,
            "r",
            encoding="utf-8",
        ) as file:
            state = json.load(file)

        return state.get("last_run_date")

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None


def save_last_run_date(
    run_date,
    state_file=AUTO_EOD_STATE_FILE,
):
    """
    Persist the most recent successful automatic EOD date.
    """

    state = {
        "last_run_date": run_date,
    }

    with open(
        state_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=4,
        )


def should_run_automatic_eod(
    current_datetime=None,
    state_file=AUTO_EOD_STATE_FILE,
):
    """
    Return True only once per TSX trading day,
    five minutes after that day's market close.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    current_date = current_datetime.date()

    if not is_tsx_trading_day(
        current_date
    ):
        return False

    market_close_time = get_tsx_market_close_time(
        current_date
    )

    automatic_eod_time = current_datetime.replace(
        hour=market_close_time.hour,
        minute=market_close_time.minute,
        second=0,
        microsecond=0,
    ) + timedelta(
        minutes=AUTO_EOD_DELAY_MINUTES
    )

    if current_datetime < automatic_eod_time:
        return False

    current_date_text = (
        current_date.isoformat()
    )

    last_run_date = load_last_run_date(
        state_file=state_file,
    )

    return last_run_date != current_date_text

def run_pipeline_validation(
    state_file=AUTO_EOD_STATE_FILE,
):
    """
    Run the read-only trading pipeline validator and save an
    immutable JSON report.

    Validation failures are returned to the EOD service rather
    than raising an exception that could crash the worker.
    """

    try:
        (
            report,
            portfolio,
            journal_rows,
            pending_rows,
            eod_state,
        ) = run_validation(
            eod_state_file=Path(state_file),
        )

        report.print_report()

        source_data_loaded = all(
            item is not None
            for item in (
                portfolio,
                journal_rows,
                pending_rows,
                eod_state,
            )
        )

        if not source_data_loaded:
            return {
                "success": False,
                "status": report.overall_status,
                "report_path": None,
                "message": (
                    "Validation report was not saved because "
                    "one or more source files could not be loaded."
                ),
            }

        report_path = save_validation_report(
            report,
            portfolio=portfolio,
            journal_rows=journal_rows,
            pending_rows=pending_rows,
            eod_state=eod_state,
        )

        return {
            "success": report.overall_status != "FAIL",
            "status": report.overall_status,
            "report_path": str(report_path),
            "message": (
                "Trading pipeline validation completed with "
                f"status {report.overall_status}."
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "status": "ERROR",
            "report_path": None,
            "message": (
                "Unexpected trading pipeline validation error: "
                f"{error}"
            ),
        }
def run_52_week_shadow_scan(
    paper_engine=None,
    measurement_date=None,
):
    """
    Run the 52-week breakout scan.

    Results are always saved for research. READY signals are
    queued only when a dedicated paper engine is supplied.
    """

    if measurement_date is None:
        measurement_date = (
            datetime.now()
            .date()
            .isoformat()
        )

    watchlist = load_all_watchlists()

    results = scan_52_week_breakouts(
        watchlist,
        signal_date=measurement_date,
    )

    report_path = save_52_week_results(
        results,
        signal_date=measurement_date,
    )

    queue_summary = {
        "attempted": 0,
        "added": 0,
        "rejected": 0,
        "results": [],
    }

    pending_total = 0

    if paper_engine is not None:
        queue_summary = paper_engine.queue_eod_signals(
            results
        )
        pending_total = len(
            paper_engine.pending_trades.get_all()
        )
    
    return {
    
        "success": True,
        "results": results,
        "ready": len(results["ready"]),
        "watch": len(results["watch"]),
        "ignored": len(results["ignore"]),
        "errors": len(results["errors"]),
        "queued": queue_summary["added"],
        "duplicates": queue_summary["rejected"],
        "already_open": queue_summary.get(
            "already_open",
            0,
        ),
        "already_pending": queue_summary.get(
            "already_pending",
            0,
        ),
        "other_rejected": queue_summary.get(
            "other_rejected",
            0,
        ),
        "pending_total": pending_total,
        "queue_summary": queue_summary,
        "report_path": report_path,
    }

def run_mean_reversion_shadow_scan(
    paper_engine=None,
    measurement_date=None,
    market_regime_provider=calculate_market_regime,
):
    """
    Run the Mean Reversion scan.

    Raw results are always preserved for research.

    NEW Mean Reversion entries pass through the broad-market
    guard before they are allowed into the pending queue.
    Existing positions are not affected.
    """

    if measurement_date is None:
        measurement_date = (
            datetime.now()
            .date()
            .isoformat()
        )

    watchlist = load_all_watchlists()

    results = scan_mean_reversion(
        watchlist,
        measurement_date=measurement_date,
    )

    # Preserve the unmodified strategy output for research.
    report_path = save_mean_reversion_results(
        results,
        measurement_date=measurement_date,
    )

    if paper_engine is None:
        # Research/live scanner path only.
        # Do not perform a historical market-regime lookup
        # when there is no executable queue to protect.
        guarded_result = {
            "guard": {
                "allow_new_entries": None,
                "guard_status": "NOT_EVALUATED",
                "market_regime": "N/A",
                "reason": (
                    "No paper engine supplied; "
                    "market guard not required."
                ),
            },
            "queue_results": {
                "ready": [],
                "watch": [],
                "ignore": [],
                "errors": [],
            },
            "blocked_ready_count": 0,
            "blocked_ready": [],
        }

    else:
        try:
            regime_result = (
                market_regime_provider(
                    measurement_date
                )
            )

        except Exception as error:
            regime_result = {
                "status": "UNAVAILABLE",
                "regime": "",
                "reason": str(error),
            }

        guarded_result = (
            build_guarded_mean_reversion_queue_results(
                results,
                regime_result,
            )
        )

    guard_research_capture = {
        "success": True,
        "status": "NOT_REQUESTED",
        "report_path": None,
        "rows_saved": 0,
        "blocked_ready_count": 0,
    }

    try:
        guard_research_capture = (
            save_mean_reversion_guard_research(
                raw_results=results,
                guarded_result=guarded_result,
                measurement_date=(
                    measurement_date
                ),
            )
        )

    except Exception as error:
        guard_research_capture = {
            "success": False,
            "status": "ERROR",
            "report_path": None,
            "rows_saved": 0,
            "blocked_ready_count": 0,
            "message": str(
                error
            ),
        }

        print(
            "Mean Reversion guard research warning: "
            f"{error}"
        )

    queue_results = guarded_result[
        "queue_results"
    ]

    queue_summary = {
        "attempted": 0,
        "added": 0,
        "rejected": 0,
        "results": [],
    }

    pending_total = 0

    if paper_engine is not None:
        queue_summary = (
            paper_engine.queue_eod_signals(
                queue_results
            )
        )

        pending_total = len(
            paper_engine
            .pending_trades
            .get_all()
        )

    return {
        "success": True,
        "results": results,
        "ready": len(
            results["ready"]
        ),
        "watch": len(
            results["watch"]
        ),
        "ignored": len(
            results["ignore"]
        ),
        "errors": len(
            results["errors"]
        ),
        "queued": queue_summary[
            "added"
        ],
        "duplicates": queue_summary[
            "rejected"
        ],
        "already_open": (
            queue_summary.get(
                "already_open",
                0,
            )
        ),
        "already_pending": (
            queue_summary.get(
                "already_pending",
                0,
            )
        ),
        "other_rejected": (
            queue_summary.get(
                "other_rejected",
                0,
            )
        ),
        "pending_total": pending_total,
        "queue_summary": queue_summary,
        "report_path": report_path,
        "market_guard": guarded_result[
            "guard"
        ],
        "market_guard_blocked": (
            guarded_result[
                "blocked_ready_count"
            ]
        ),
        "queue_ready": len(
            queue_results["ready"]
        ),
        "market_guard_research": (
            guard_research_capture
        ),
    }


def build_scan_results_from_live_snapshot(
    live_quotes,
    signal_date,
):
    """
    Convert live workstation quotes into the standard EOD
    signal format used by the paper-trading queue.
    """

    results = {
        "ready": [],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    for quote in live_quotes:
        try:
            signal = {
                "symbol": quote["symbol"],
                "strategy": "MOMENTUM",
                "signal_date": signal_date,
                "close": float(quote["price"]),
                "atr": float(quote["atr"]),
                "tmqs": float(quote["tmqs"]),
                "rvol": float(
                    quote["relative_volume"]
                ),
                "breakout": quote["breakout_status"],
                "decision": quote["decision"],
                "reason": quote.get("reason", ""),
            }

            decision = signal["decision"]

            if decision == "READY":
                results["ready"].append(signal)
            elif decision == "WATCH":
                results["watch"].append(signal)
            else:
                results["ignore"].append(signal)

        except Exception as error:
            results["errors"].append(
                {
                    "symbol": quote.get(
                        "symbol",
                        "UNKNOWN",
                    ),
                    "message": str(error),
                }
            )

    return results
def run_restore_verification_after_backup(
    backup_result,
    current_datetime=None,
    runner=run_restore_test_if_due,
):
    """
    Run monthly disaster-recovery verification only
    after a successful physical/external backup.

    Daily local backups and local fallback backups do
    not trigger a restore test.
    """

    if not isinstance(
        backup_result,
        dict,
    ):
        return {
            "success": False,
            "status": "ERROR",
            "ran": False,
            "errors": [
                "Backup result is not a dictionary."
            ],
        }

    if not backup_result.get(
        "success",
        False,
    ):
        return {
            "success": True,
            "status": "NOT_APPLICABLE",
            "ran": False,
            "errors": [],
        }

    if (
        backup_result.get(
            "backup_type"
        )
        != "EXTERNAL"
    ):
        return {
            "success": True,
            "status": "NOT_APPLICABLE",
            "ran": False,
            "errors": [],
        }

    backup_path = backup_result.get(
        "backup_path"
    )

    if not backup_path:
        return {
            "success": False,
            "status": "ERROR",
            "ran": False,
            "errors": [
                (
                    "External backup succeeded but "
                    "no backup path was reported."
                )
            ],
        }

    try:
        result = runner(
            backup_path=backup_path,
            current_datetime=(
                current_datetime
            ),
        )

    except Exception as error:
        return {
            "success": False,
            "status": "ERROR",
            "ran": False,
            "backup_path": backup_path,
            "errors": [
                str(error)
            ],
        }

    if not isinstance(
        result,
        dict,
    ):
        return {
            "success": False,
            "status": "ERROR",
            "ran": False,
            "backup_path": backup_path,
            "errors": [
                (
                    "Restore-test runner did not "
                    "return a result dictionary."
                )
            ],
        }

    return result


def run_cloud_backup_after_eod(
    current_datetime=None,
    runner=None,
):
    """
    Run the encrypted off-site cloud backup
    without allowing cloud availability to
    interfere with the trading EOD cycle.
    """

    if runner is None:
        return {
            "success": True,
            "status": "NOT_REQUESTED",
            "ran": False,
            "errors": [],
        }

    try:
        # Cloud backups represent the actual
        # disaster-recovery copy time.
        #
        # Never pass the EOD cycle timestamp here:
        # recovery EOD cycles may intentionally use
        # an older historical datetime, which would
        # incorrectly backdate cloud backup health.
        result = runner()

    except Exception as error:
        return {
            "success": False,
            "status": "ERROR",
            "ran": True,
            "backup_path": None,
            "errors": [
                str(error)
            ],
        }

    if not isinstance(
        result,
        dict,
    ):
        return {
            "success": False,
            "status": "ERROR",
            "ran": True,
            "backup_path": None,
            "errors": [
                (
                    "Cloud backup runner did not "
                    "return a result dictionary."
                )
            ],
        }

    result["ran"] = True

    return result


def run_automatic_eod_cycle(
    paper_engine,
    breakout_52week_engine=None,
    mean_reversion_engine=None,
    current_datetime=None,
    state_file=AUTO_EOD_STATE_FILE,
    scan_provider=scan_eod_signals,
    live_snapshot_provider=None,
    validation_runner=run_pipeline_validation,
    shadow_scan_runner=run_52_week_shadow_scan,
    mean_reversion_runner=run_mean_reversion_shadow_scan,
    candidate_history_runner=None,
    momentum_research_saver=None,
    forward_outcome_runner=None,
    time_exit_runner=run_eod_time_exits,
    cloud_backup_runner=None,
):
    """
    Run one automatic EOD cycle when eligible.

    The completion date is persisted only after the scan and
    queue workflow finish successfully.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    current_date = current_datetime.date().isoformat()

    if not should_run_automatic_eod(
        current_datetime=current_datetime,
        state_file=state_file,
    ):
        return {
            "success": True,
        
            "status": "NOT_DUE",
            "run_date": current_date,
            "message": (
                "Automatic EOD scan is not due."
            ),
        }
    
    strategy_engines = {
        "momentum": paper_engine,
        "52_week_breakout": (
            breakout_52week_engine
        ),
        "mean_reversion": (
            mean_reversion_engine
        ),
    }

    time_exit_result = time_exit_runner(
        engines=strategy_engines,
        current_date=current_date,
    )

    if not time_exit_result.get(
        "success",
        False,
    ):
        return {
            "success": False,
            "status": "TIME_EXIT_FAILED",
            "run_date": current_date,
            "time_exits": time_exit_result,
            "message": (
                "End-of-day maximum-hold "
                "exit processing failed."
            ),
        }

    live_quotes = []

    if live_snapshot_provider is not None:
        try:
            live_quotes = live_snapshot_provider()
        except Exception:
            live_quotes = []

    try:
        results = scan_provider(
            current_datetime=current_datetime,
        )
    except Exception:
        if live_quotes:
            results = build_scan_results_from_live_snapshot(
                live_quotes,
                current_date,
            )
        else:
            raise
    from paper_trading.signal_journal import record_ready_signals

    record_ready_signals(
        results["ready"],
        current_datetime.date(),
    )

    momentum_research_capture = {
        "success": True,
        "status": "NOT_REQUESTED",
        "report_path": None,
        "rows_saved": 0,
        "error_rows": 0,
    }

    if momentum_research_saver is not None:
        try:
            momentum_research_capture = (
                momentum_research_saver(
                    results=results,
                    signal_date=current_date,
                    captured_at=current_datetime,
                )
            )
        except Exception as error:
            momentum_research_capture = {
                "success": False,
                "status": "ERROR",
                "report_path": None,
                "rows_saved": 0,
                "error_rows": 0,
                "message": str(error),
            }

            print(
                "Momentum research capture warning: "
                f"{error}"
            )
    
    queue_summary = paper_engine.queue_eod_signals(
        results
    )

    momentum_pending_total = (
        get_pending_trade_count(
            paper_engine,
            fallback=queue_summary.get(
                "added",
                0,
            ),
        )
    )

    summary = {
        "success": True,
        "status": "COMPLETED",
        "run_date": current_date,
        "ready": len(results["ready"]),
        "watch": len(results["watch"]),
        "ignored": len(results["ignore"]),
        "errors": len(results["errors"]),
        "queued": queue_summary["added"],
        "duplicates": queue_summary["rejected"],
        "pending_total": momentum_pending_total,
        "scan_results": results,
        "queue_summary": queue_summary,
        "momentum_research_capture": (
            momentum_research_capture
        ),
        "time_exits": time_exit_result,
    }
    
    try:
        try:
            shadow_result = shadow_scan_runner(
                paper_engine=breakout_52week_engine,
                measurement_date=current_date,
            )

        except TypeError as error:
            error_text = str(
                error
            )

            if (
                "measurement_date"
                in error_text
            ):
                try:
                    shadow_result = (
                        shadow_scan_runner(
                            paper_engine=(
                                breakout_52week_engine
                            ),
                        )
                    )

                except TypeError as nested_error:
                    if (
                        "paper_engine"
                        not in str(
                            nested_error
                        )
                    ):
                        raise

                    shadow_result = (
                        shadow_scan_runner()
                    )

            elif (
                "paper_engine"
                in error_text
            ):
                shadow_result = (
                    shadow_scan_runner()
                )

            else:
                raise

    except Exception as error:
        shadow_result = {
            "success": False,
            "ready": 0,
            "watch": 0,
            "ignored": 0,
            "errors": 1,
            "report_path": None,
            "message": str(error),
        }

    summary["breakout_52week_shadow"] = shadow_result

    try:
        try:
            mean_reversion_result = mean_reversion_runner(
                paper_engine=mean_reversion_engine,
                measurement_date=current_date,
            )

        except TypeError as error:
            if "measurement_date" not in str(error):
                raise

            mean_reversion_result = mean_reversion_runner(
                paper_engine=mean_reversion_engine,
            )

    except Exception as error:
        mean_reversion_result = {
            "success": False,
            "ready": 0,
            "watch": 0,
            "ignored": 0,
            "errors": 1,
            "report_path": None,
            "message": str(error),
        }

    summary["mean_reversion_shadow"] = (
        mean_reversion_result
    )

    forward_outcome_result = (
        run_forward_outcome_research_capture(
            runner=forward_outcome_runner,
            current_date=current_date,
        )
    )

    summary[
        "candidate_forward_outcomes"
    ] = forward_outcome_result

    if not forward_outcome_result.get(
        "success",
        False,
    ):
        print(
            "Candidate forward-outcome research warning: "
            f"{forward_outcome_result.get('message', '')}"
        )

    save_last_run_date(
        current_date,
        state_file=state_file,
    )

    validation_result = validation_runner(
        state_file=state_file,
    )

    summary["validation"] = validation_result

    if candidate_history_runner is None:
        candidate_history_result = {
            "success": True,
            "status": "NOT_REQUESTED",
            "strategies": {},
        }
    else:
        try:
            candidate_history_result = (
                candidate_history_runner()
            )
        except Exception as error:
            candidate_history_result = {
                "success": False,
                "status": "ERROR",
                "strategies": {},
                "message": (
                    "Candidate history capture failed: "
                    f"{error}"
                ),
            }

    summary["candidate_history"] = (
        candidate_history_result
    )
    

    try:
        backup_result = create_backup()
    except Exception as error:
        backup_result = {
            "success": False,
            "enabled": True,
            "backup_path": None,
            "copied": 0,
            "skipped": 0,
            "errors": [str(error)],
        }

    summary["backup"] = backup_result

    cloud_backup_result = (
        run_cloud_backup_after_eod(
            current_datetime=current_datetime,
            runner=cloud_backup_runner,
        )
    )

    summary["cloud_backup"] = (
        cloud_backup_result
    )

    if not cloud_backup_result.get(
        "success",
        False,
    ):
        print(
            "Encrypted cloud backup warning: "
            + "; ".join(
                cloud_backup_result.get(
                    "errors",
                    [],
                )
            )
        )

    restore_test_result = (
        run_restore_verification_after_backup(
            backup_result=backup_result,
            current_datetime=current_datetime,
        )
    )

    summary["restore_test"] = (
        restore_test_result
    )

    if not restore_test_result.get(
        "success",
        False,
    ):
        print(
            "Monthly restore verification warning: "
            + "; ".join(
                restore_test_result.get(
                    "errors",
                    [],
                )
            )
        )

    if validation_result["report_path"]:
        print(
            "Validation report saved: "
            f"{validation_result['report_path']}"
        )

    if not validation_result["success"]:
        print(
            "Trading pipeline validation warning: "
            f"{validation_result['message']}"
        )
    momentum_status = (
        "PASS"
        if summary["errors"] == 0
        else "FAIL"
    )

    breakout_status = (
        "PASS"
        if (
            shadow_result.get("success", False)
            and shadow_result.get("errors", 0) == 0
        )
        else "FAIL"
    )

    mean_reversion_status = (
        "PASS"
        if (
            mean_reversion_result.get("success", False)
            and mean_reversion_result.get("errors", 0) == 0
        )
        else "FAIL"
    )

    validation_status = validation_result["status"]

    backup_status = (
        "PASS"
        if backup_result["success"]
        else "FAIL"
    )

    core_eod_warning = (
        momentum_status != "PASS"
        or breakout_status != "PASS"
        or mean_reversion_status != "PASS"
        or validation_status == "FAIL"
    )

    only_backup_warning = (
        not core_eod_warning
        and backup_status != "PASS"
    )

    has_eod_warning = (
        core_eod_warning
        or backup_status != "PASS"
    )

    if only_backup_warning:
        overall_health = "WARNING - BACKUP ONLY"
        telegram_heading = (
            "NORTHSTAR QUANT EOD COMPLETE - "
            "BACKUP WARNING"
        )
    elif has_eod_warning:
        overall_health = "WARNING"
        telegram_heading = (
            "NORTHSTAR QUANT EOD WARNING"
        )
    else:
        overall_health = "HEALTHY"
        telegram_heading = (
            "NORTHSTAR QUANT EOD COMPLETE"
        )

    backup_errors = backup_result.get("errors", [])

    if backup_errors:
        backup_error_detail = "\n".join(
            f"- {error}"
            for error in backup_errors[:3]
        )

        if len(backup_errors) > 3:
            backup_error_detail += (
                "\n- ... and "
                f"{len(backup_errors) - 3} more error(s)"
            )
    else:
        backup_error_detail = "None"

    breakout_pending_total = (
        get_pending_trade_count(
            breakout_52week_engine,
            fallback=shadow_result.get(
                "pending_total",
                0,
            ),
        )
    )

    mean_reversion_pending_total = (
        get_pending_trade_count(
            mean_reversion_engine,
            fallback=mean_reversion_result.get(
                "pending_total",
                0,
            ),
        )
    )

    total_pending = (
        momentum_pending_total
        + breakout_pending_total
        + mean_reversion_pending_total
    )

    summary["total_pending"] = total_pending

    pending_execution_footer = (
        build_pending_execution_footer(
            total_pending
        )
    )

    telegram_message = (
        f"{telegram_heading}\n\n"
        f"Date: {current_date}\n\n"

        "MOMENTUM\n"
        f"Status: {momentum_status}\n"
        f"READY: {summary['ready']}\n"
        f"Queued: {summary['queued']}\n"
        f"Total Pending: {momentum_pending_total}\n"
        f"WATCH: {summary['watch']}\n"
        f"Errors: {summary['errors']}\n\n"

        "52-WEEK BREAKOUT\n"
        f"Status: {breakout_status}\n"
        f"READY: {shadow_result.get('ready', 0)}\n"
        f"Newly Queued: {shadow_result.get('queued', 0)}\n"
        f"Already Open: {shadow_result.get('already_open', 0)}\n"
        f"Already Pending: {shadow_result.get('already_pending', 0)}\n"
        f"Other Rejected: {shadow_result.get('other_rejected', 0)}\n"
        f"Total Pending: {breakout_pending_total}\n"
        f"WATCH: {shadow_result.get('watch', 0)}\n"
        f"Errors: {shadow_result.get('errors', 0)}\n\n"

        "MEAN REVERSION\n"
        f"Status: {mean_reversion_status}\n"
        f"READY: {mean_reversion_result.get('ready', 0)}\n"
        f"Market Guard: "
        f"{mean_reversion_result.get('market_guard', {}).get('guard_status', 'N/A')} "
        f"({mean_reversion_result.get('market_guard', {}).get('market_regime', 'N/A')})\n"
        f"Queue-Eligible READY: {mean_reversion_result.get('queue_ready', 0)}\n"
        f"Guard-Blocked READY: {mean_reversion_result.get('market_guard_blocked', 0)}\n"
        f"Newly Queued: {mean_reversion_result.get('queued', 0)}\n"
        f"Already Open: {mean_reversion_result.get('already_open', 0)}\n"
        f"Already Pending: {mean_reversion_result.get('already_pending', 0)}\n"
        f"Other Rejected: {mean_reversion_result.get('other_rejected', 0)}\n"
        f"Total Pending: {mean_reversion_pending_total}\n"
        f"WATCH: {mean_reversion_result.get('watch', 0)}\n"
        f"Errors: {mean_reversion_result.get('errors', 0)}\n\n"

        "SYSTEM CHECKS\n"
        f"Pipeline Validation: {validation_status}\n"
        f"Backup: {backup_status}\n"
        f"Backup Items Copied: {backup_result.get('copied', 0)}\n"
        f"Backup Items Skipped: {backup_result.get('skipped', 0)}\n"
        f"Backup Errors: {len(backup_errors)}\n"
        "Backup Error Detail:\n"
        f"{backup_error_detail}\n\n"

        f"OVERALL HEALTH: {overall_health}\n\n"
        f"{pending_execution_footer}"
    )

    try:
        telegram_result = send_telegram_message(
            telegram_message
        )
    except Exception as error:
        telegram_result = {
            "success": False,
            "message": (
                "Unexpected Telegram notification error: "
                f"{error}"
            ),
        }

    summary["telegram"] = telegram_result

    if not telegram_result["success"]:
        print(
            "Telegram notification warning: "
            f"{telegram_result['message']}"
        )

    
    print("\n" + "=" * 60)
    print("AUTOMATIC END-OF-DAY SCAN")
    print("=" * 60)
    print(f"Run date   : {current_date}")
    print(f"READY      : {summary['ready']}")
    print(f"Queued     : {summary['queued']}")
    print(f"Duplicates : {summary['duplicates']}")
    print(f"WATCH      : {summary['watch']}")
    print(f"IGNORE     : {summary['ignored']}")
    print(f"Errors     : {summary['errors']}")
    print(
        "Validation : "
        f"{validation_result['status']}"
    )

    if validation_result["report_path"]:
        print(
            "Report     : "
            f"{validation_result['report_path']}"
        )

    print("=" * 60)

    return summary



def automatic_eod_worker(
    paper_engine,
    breakout_52week_engine=None,
    mean_reversion_engine=None,
    check_seconds=DEFAULT_CHECK_SECONDS,
    stop_event=None,
    live_snapshot_provider=None,
):
    """
    Continuously check whether an EOD scan is due.

    The worker also reconciles the most recent missed TSX EOD
    workflow when recovery is still safe before the next market
    session begins.
    """

    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            current_datetime = (
                normalize_current_datetime()
            )

            last_run_date = load_last_run_date()

            recovery_datetime = (
                get_recoverable_eod_datetime(
                    current_datetime=current_datetime,
                    last_run_date=last_run_date,
                )
            )

            cycle_datetime = (
                recovery_datetime
                if recovery_datetime is not None
                else current_datetime
            )

            result = run_automatic_eod_cycle(
                paper_engine=paper_engine,
                breakout_52week_engine=breakout_52week_engine,
                mean_reversion_engine=mean_reversion_engine,
                current_datetime=cycle_datetime,
                live_snapshot_provider=(
                    live_snapshot_provider
                ),
                candidate_history_runner=(
                    capture_all_candidate_history
                ),
                momentum_research_saver=(
                    save_momentum_universe_snapshot
                ),
                forward_outcome_runner=(
                    run_candidate_forward_outcome_refresh
                ),
                cloud_backup_runner=(
                    create_cloud_backup
                ),
            )

            if (
                recovery_datetime is not None
                and result.get("status")
                == "COMPLETED"
            ):
                print(
                    "Recovered missed automatic EOD "
                    f"workflow for "
                    f"{recovery_datetime.date().isoformat()}."
                )

        except Exception as error:
            print(
                "Automatic EOD scan error: "
                f"{error}"
            )

        stop_event.wait(check_seconds)


def start_automatic_eod_service(
    paper_engine,
    breakout_52week_engine=None,
    mean_reversion_engine=None,
    check_seconds=DEFAULT_CHECK_SECONDS,
    live_snapshot_provider=None,
):
    """
    Start the automatic EOD service in a daemon thread.
    """

    thread = threading.Thread(
        target=automatic_eod_worker,
        kwargs={
            "paper_engine": paper_engine,
            "breakout_52week_engine": breakout_52week_engine,
            "mean_reversion_engine": mean_reversion_engine,
            "check_seconds": check_seconds,
            "live_snapshot_provider": (
                live_snapshot_provider
            ),
        },
        daemon=True,
        name="automatic-eod-service",
    )
    thread.start()

    return thread