"""
Mean Reversion Market Guard

Broad-market risk gate for NEW Mean Reversion entries.

This module does not change the underlying Mean Reversion
strategy signal. It only determines whether a new READY signal
is permitted to enter the pending-trade queue.

Momentum and 52-Week Breakout do not use this guard.
"""


def evaluate_mean_reversion_market_guard(
    regime_result,
):
    """
    Decide whether new Mean Reversion entries are permitted.

    Fail closed:
    - BULL       -> allow
    - SIDEWAYS   -> allow
    - BEAR       -> block
    - unavailable/unknown regime -> block
    """

    if not isinstance(
        regime_result,
        dict,
    ):
        return {
            "allow_new_entries": False,
            "guard_status": "BLOCKED",
            "market_regime": "UNAVAILABLE",
            "reason": (
                "Market regime unavailable. "
                "New Mean Reversion entries blocked."
            ),
        }

    regime_status = str(
        regime_result.get(
            "status",
            "",
        )
    ).strip().upper()

    market_regime = str(
        regime_result.get(
            "regime",
            "",
        )
    ).strip().upper()

    if regime_status != "AVAILABLE":
        return {
            "allow_new_entries": False,
            "guard_status": "BLOCKED",
            "market_regime": (
                market_regime
                or "UNAVAILABLE"
            ),
            "reason": (
                "Market regime unavailable. "
                "New Mean Reversion entries blocked."
            ),
        }

    if market_regime == "BEAR":
        return {
            "allow_new_entries": False,
            "guard_status": "BLOCKED",
            "market_regime": market_regime,
            "reason": (
                "Broad TSX market regime is BEAR. "
                "New Mean Reversion entries blocked."
            ),
        }

    if market_regime in {
        "BULL",
        "SIDEWAYS",
    }:
        return {
            "allow_new_entries": True,
            "guard_status": "PASS",
            "market_regime": market_regime,
            "reason": (
                "Broad-market regime permits "
                "new Mean Reversion entries."
            ),
        }

    return {
        "allow_new_entries": False,
        "guard_status": "BLOCKED",
        "market_regime": (
            market_regime
            or "UNKNOWN"
        ),
        "reason": (
            "Unknown market regime. "
            "New Mean Reversion entries blocked."
        ),
    }


def build_guarded_mean_reversion_queue_results(
    scan_results,
    regime_result,
):
    """
    Build the Mean Reversion results that are allowed to reach
    the pending-trade queue.

    The original scan_results dictionary is never modified.

    When the market guard blocks new entries:
    - raw READY signals are removed from queue-ready results
    - those signals are copied into WATCH
    - the original READY research signal remains untouched
    """

    guard_result = (
        evaluate_mean_reversion_market_guard(
            regime_result
        )
    )

    queue_results = {
        "ready": [
            dict(item)
            for item in scan_results.get(
                "ready",
                [],
            )
        ],
        "watch": [
            dict(item)
            for item in scan_results.get(
                "watch",
                [],
            )
        ],
        "ignore": [
            dict(item)
            for item in scan_results.get(
                "ignore",
                [],
            )
        ],
        "errors": [
            dict(item)
            for item in scan_results.get(
                "errors",
                [],
            )
        ],
    }

    blocked_ready = []

    if not guard_result[
        "allow_new_entries"
    ]:
        for trade in queue_results["ready"]:
            blocked_trade = dict(trade)

            blocked_trade[
                "raw_decision"
            ] = trade.get(
                "decision",
                "READY",
            )

            blocked_trade[
                "decision"
            ] = "WATCH"

            blocked_trade[
                "market_guard_status"
            ] = guard_result[
                "guard_status"
            ]

            blocked_trade[
                "market_regime"
            ] = guard_result[
                "market_regime"
            ]

            blocked_trade[
                "market_guard_reason"
            ] = guard_result[
                "reason"
            ]

            blocked_ready.append(
                blocked_trade
            )

        queue_results["ready"] = []

        queue_results["watch"].extend(
            blocked_ready
        )

    return {
        "guard": guard_result,
        "queue_results": queue_results,
        "blocked_ready_count": len(
            blocked_ready
        ),
        "blocked_ready": blocked_ready,
    }
