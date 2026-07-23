"""
Automatic End-of-Day Signal Service

Runs the production EOD scanner once per eligible trading day
after the TSX closes, queues READY signals, and records the date
so application refreshes or restarts do not repeat the scan.

The service runs in a background daemon thread so it does not
block the Trading Workstation.
"""
from utilities.backup_manager import create_backup
from datetime import datetime
import json
import os
from pathlib import Path
import threading

from core.eod_signal_service import scan_eod_signals
from core.market_hours import (
    MARKET_CLOSE_TIME,
    TORONTO_TIMEZONE,
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
from paper_trading.trading_pipeline_validator import (
    run_validation,
    save_validation_report,
)

from paper_trading.signal_journal import record_ready_signals

AUTO_EOD_STATE_FILE = "automatic_eod_state.json"
DEFAULT_CHECK_SECONDS = 60


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
    Return True only once per weekday after the TSX closes.
    """

    current_datetime = normalize_current_datetime(
        current_datetime
    )

    if current_datetime.weekday() >= 5:
        return False

    current_time = (
        current_datetime.time().replace(tzinfo=None)
    )

    if current_time < MARKET_CLOSE_TIME:
        return False

    current_date = current_datetime.date().isoformat()

    last_run_date = load_last_run_date(
        state_file=state_file,
    )

    return last_run_date != current_date

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
def run_52_week_shadow_scan():
    """
    Run the 52-week strategy in research-only shadow mode.

    This function does not queue or execute any paper trades.
    """

    watchlist = load_all_watchlists()
    results = scan_52_week_breakouts(watchlist)
    report_path = save_52_week_results(results)

    return {
        "success": True,
        "ready": len(results["ready"]),
        "watch": len(results["watch"]),
        "ignored": len(results["ignore"]),
        "errors": len(results["errors"]),
        "report_path": report_path,
    }
def run_mean_reversion_shadow_scan():
    """
    Run the Mean Reversion strategy in research-only shadow mode.

    This function does not queue or execute any paper trades.
    """

    watchlist = load_all_watchlists()
    results = scan_mean_reversion(watchlist)
    report_path = save_mean_reversion_results(results)

    return {
        "success": True,
        "ready": len(results["ready"]),
        "watch": len(results["watch"]),
        "ignored": len(results["ignore"]),
        "errors": len(results["errors"]),
        "report_path": report_path,
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
def run_automatic_eod_cycle(
    paper_engine,
    current_datetime=None,
    state_file=AUTO_EOD_STATE_FILE,
    scan_provider=scan_eod_signals,
    live_snapshot_provider=None,
    validation_runner=run_pipeline_validation,
    shadow_scan_runner=run_52_week_shadow_scan,
    mean_reversion_runner=run_mean_reversion_shadow_scan,
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
    
    queue_summary = paper_engine.queue_eod_signals(
        results
    )
    save_last_run_date(
        current_date,
        state_file=state_file,
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
        "scan_results": results,
        "queue_summary": queue_summary,
    }
    validation_result = validation_runner(
        state_file=state_file,
    )

    summary["validation"] = validation_result

    try:
        shadow_result = shadow_scan_runner()
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
        mean_reversion_result = mean_reversion_runner()
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
    has_eod_warning = (
        summary["errors"] > 0
        or validation_result["status"] != "PASS"
        or not backup_result["success"]
    )

    telegram_heading = (
        "AUTOMATIC EOD WARNING"
        if has_eod_warning
        else "AUTOMATIC EOD SCAN COMPLETED"
    )
    telegram_message = (
        f"{telegram_heading}\n\n"
        f"Date: {current_date}\n"
        f"READY: {summary['ready']}\n"
        f"Queued: {summary['queued']}\n"
        f"Duplicates: {summary['duplicates']}\n"
        f"WATCH: {summary['watch']}\n"
        f"IGNORE: {summary['ignored']}\n"
        f"Errors: {summary['errors']}\n"
        f"Pipeline Validation: "
        f"{validation_result['status']}\n"
        f"Backup: "
        f"{'SUCCESS' if backup_result['success'] else 'FAILED'}\n"
        f"Backup Items Copied: "
        f"{backup_result['copied']}\n"
        f"Backup Errors: "
        f"{len(backup_result['errors'])}\n\n"
        "Pending signals are ready for next-day execution."
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
    check_seconds=DEFAULT_CHECK_SECONDS,
    stop_event=None,
    live_snapshot_provider=None,
):
    """
    Continuously check whether the daily EOD scan is due.
    """

    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            run_automatic_eod_cycle(
                paper_engine=paper_engine,
                live_snapshot_provider=live_snapshot_provider,
            )

        except Exception as error:
            print(
                "Automatic EOD scan error: "
                f"{error}"
            )

        stop_event.wait(check_seconds)


def start_automatic_eod_service(
    paper_engine,
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