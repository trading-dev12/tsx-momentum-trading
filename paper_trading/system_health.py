"""
Paper Trading System Health

Builds a concise, colour-indicated operational status report
for the automated paper-trading services and persistent state.
"""

import os


GREEN = "🟢"
YELLOW = "🟡"
RED = "🔴"


def thread_status(thread):
    """
    Return the status text and indicator for a background thread.
    """

    if thread is None:
        return RED, "NOT STARTED"

    if thread.is_alive():
        return GREEN, "RUNNING"

    return RED, "STOPPED"


def journal_status(
    journal_file="paper_trade_journal.csv",
):
    """
    Report whether the journal folder is writable.
    """

    folder = os.path.dirname(
        os.path.abspath(journal_file)
    )

    if os.access(folder, os.W_OK):
        return GREEN, "READY"

    return RED, "NOT WRITABLE"


def scanner_status(scanner_refreshing):
    """
    Return the current scanner state.
    """

    if scanner_refreshing:
        return YELLOW, "REFRESHING"

    return GREEN, "RUNNING"


def position_monitor_status(open_positions):
    """
    Return the position-monitor state.
    """

    if open_positions > 0:
        return GREEN, "ACTIVE"

    return YELLOW, "WAITING"


def build_system_health_text(
    paper_engine,
    automatic_execution_thread=None,
    automatic_eod_thread=None,
    scanner_refreshing=False,
    last_refresh=None,
):
    """
    Build the workstation System Health display.
    """

    scanner_icon, scanner_text = scanner_status(
        scanner_refreshing
    )

    execution_icon, execution_text = thread_status(
        automatic_execution_thread
    )

    eod_icon, eod_text = thread_status(
        automatic_eod_thread
    )

    journal_icon, journal_text = journal_status()

    open_positions = len(
        paper_engine.portfolio.open_positions
    )

    pending_trades = len(
        paper_engine.pending_trades.get_all()
    )

    closed_trades = len(
        paper_engine.portfolio.closed_trades
    )

    monitor_icon, monitor_text = position_monitor_status(
        open_positions
    )

    if last_refresh is None:
        last_refresh_text = "--"
    else:
        last_refresh_text = str(last_refresh)

    divider = "-" * 34

    lines = [
        "SYSTEM HEALTH",
        divider,
        (
            f"{scanner_icon} Scanner "
            f"{scanner_text}"
        ),
        (
            f"{execution_icon} Auto Execution "
            f"{execution_text}"
        ),
        (
            f"{eod_icon} Auto EOD "
            f"{eod_text}"
        ),
        (
            f"{monitor_icon} Position Monitor "
            f"{monitor_text}"
        ),
        (
            f"{journal_icon} Trade Journal "
            f"{journal_text}"
        ),
        "",
        f"Pending Trades: {pending_trades}",
        f"Open Positions: {open_positions}",
        f"Closed Trades: {closed_trades}",
        f"Last Refresh: {last_refresh_text}",
    ]

    return "\n".join(lines)