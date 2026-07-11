"""
Automatic Paper Trade Execution Service

Runs the pending-trade execution workflow in a background
thread while the trading workstation remains open.

The service immediately checks pending trades at startup and
then retries periodically. Trades remain queued whenever an
opening price is unavailable.
"""

from datetime import datetime
import threading
import time

from paper_trading.opening_price import get_market_open_price


DEFAULT_RETRY_SECONDS = 60


def run_automatic_execution_cycle(
    paper_engine,
    execution_date=None,
    price_provider=get_market_open_price,
):
    """
    Run one automatic pending-trade execution cycle.

    This function is kept separate so it can be tested without
    starting an endless background thread.
    """

    if execution_date is None:
        execution_date = datetime.now().strftime("%Y-%m-%d")

    result = paper_engine.execute_pending_trades_for_date(
        execution_date=execution_date,
        price_provider=price_provider,
    )

    print("\n" + "=" * 60)
    print("AUTOMATIC PAPER EXECUTION")
    print("=" * 60)
    print(f"Execution date    : {result['execution_date']}")
    print(f"Pending checked   : {result['attempted']}")
    print(f"Executed          : {result['executed']}")
    print(f"Price unavailable : {result['price_unavailable']}")
    print(f"Skipped           : {result['skipped']}")
    print(f"Failed            : {result['failed']}")

    for trade_result in result["results"]:
        symbol = trade_result["symbol"]
        status = trade_result["status"]
        message = trade_result.get("message", "")

        print(
            f"{symbol:<12} "
            f"{status:<18} "
            f"{message}"
        )

    print("=" * 60)

    return result


def automatic_execution_worker(
    paper_engine,
    retry_seconds=DEFAULT_RETRY_SECONDS,
    stop_event=None,
):
    """
    Continuously retry pending paper-trade execution.

    The worker stops only when stop_event is supplied and set.
    As a daemon thread, it also stops when the application closes.
    """

    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            run_automatic_execution_cycle(
                paper_engine=paper_engine,
            )

        except Exception as error:
            print(
                "Automatic paper execution error: "
                f"{error}"
            )

        stop_event.wait(retry_seconds)


def start_automatic_execution_service(
    paper_engine,
    retry_seconds=DEFAULT_RETRY_SECONDS,
):
    """
    Start automatic paper execution in a daemon thread.
    """

    thread = threading.Thread(
        target=automatic_execution_worker,
        kwargs={
            "paper_engine": paper_engine,
            "retry_seconds": retry_seconds,
        },
        daemon=True,
        name="paper-trade-auto-execution",
    )

    thread.start()

    return thread