"""
Harmless cross-process ownership tests.

Tests:
1. Parent acquires the trading-service lock.
2. Child is refused while parent owns it.
3. New owner succeeds after normal release.
4. Separate holder process owns the lock.
5. Another process is refused while holder owns it.
6. Holder is terminated without calling release().
7. Windows releases the abandoned lock automatically.
"""

import subprocess
import sys
import time

from core.service_ownership import (
    TradingServiceOwnership,
    read_trading_service_owner,
)


if "--child" in sys.argv:
    child_owner = TradingServiceOwnership(
        "TEST_CHILD"
    )

    child_acquired = child_owner.acquire()

    print(
        f"child_acquired={child_acquired}",
        flush=True,
    )

    if child_acquired:
        child_owner.release()

    sys.exit(0)


if "--holder" in sys.argv:
    holder_owner = TradingServiceOwnership(
        "TEST_CRASH_HOLDER"
    )

    holder_acquired = holder_owner.acquire()

    print(
        f"holder_acquired={holder_acquired}",
        flush=True,
    )

    if not holder_acquired:
        sys.exit(1)

    while True:
        time.sleep(1)


parent_owner = TradingServiceOwnership(
    "TEST_PARENT"
)

parent_acquired = parent_owner.acquire()

print(
    f"parent_acquired={parent_acquired}"
)

print(
    f"owner_state={read_trading_service_owner()}"
)

if not parent_acquired:
    raise SystemExit(
        "TEST FAILED: parent could not acquire lock."
    )

child_result = subprocess.run(
    [
        sys.executable,
        "-m",
        "tools.service_ownership_check",
        "--child",
    ],
    capture_output=True,
    text=True,
)

print(
    child_result.stdout.strip()
)

if child_result.stderr.strip():
    print(
        "child_stderr="
        f"{child_result.stderr.strip()}"
    )

parent_owner.release()

after_release_owner = TradingServiceOwnership(
    "TEST_AFTER_RELEASE"
)

after_release_acquired = (
    after_release_owner.acquire()
)

print(
    f"after_release_acquired="
    f"{after_release_acquired}"
)

if after_release_acquired:
    after_release_owner.release()


holder_process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "tools.service_ownership_check",
        "--holder",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

holder_line = (
    holder_process.stdout.readline().strip()
)

print(holder_line)

time.sleep(1)

during_holder_owner = TradingServiceOwnership(
    "TEST_DURING_HOLDER"
)

during_holder_acquired = (
    during_holder_owner.acquire()
)

print(
    f"during_holder_acquired="
    f"{during_holder_acquired}"
)

if during_holder_acquired:
    during_holder_owner.release()

holder_process.terminate()

holder_process.wait(
    timeout=10
)

time.sleep(1)

after_crash_owner = TradingServiceOwnership(
    "TEST_AFTER_CRASH"
)

after_crash_acquired = (
    after_crash_owner.acquire()
)

print(
    f"after_crash_acquired="
    f"{after_crash_acquired}"
)

print(
    f"owner_state_after_crash="
    f"{read_trading_service_owner()}"
)

if after_crash_acquired:
    after_crash_owner.release()


normal_test_passed = (
    parent_acquired
    and "child_acquired=False"
    in child_result.stdout
    and after_release_acquired
)

crash_test_passed = (
    "holder_acquired=True"
    in holder_line
    and not during_holder_acquired
    and after_crash_acquired
)

if normal_test_passed:
    print(
        "NORMAL OWNERSHIP TEST: PASS"
    )
else:
    print(
        "NORMAL OWNERSHIP TEST: FAIL"
    )

if crash_test_passed:
    print(
        "CRASH RECOVERY TEST: PASS"
    )
else:
    print(
        "CRASH RECOVERY TEST: FAIL"
    )

if (
    normal_test_passed
    and crash_test_passed
):
    print(
        "ALL OWNERSHIP TESTS: PASS"
    )
else:
    print(
        "ALL OWNERSHIP TESTS: FAIL"
    )

