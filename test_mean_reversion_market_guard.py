from strategies.mean_reversion_market_guard import (
    evaluate_mean_reversion_market_guard,
)


def test_bull_market_allows_new_entries():
    result = evaluate_mean_reversion_market_guard(
        {
            "status": "AVAILABLE",
            "regime": "BULL",
        }
    )

    assert result["allow_new_entries"] is True
    assert result["guard_status"] == "PASS"
    assert result["market_regime"] == "BULL"


def test_sideways_market_allows_new_entries():
    result = evaluate_mean_reversion_market_guard(
        {
            "status": "AVAILABLE",
            "regime": "SIDEWAYS",
        }
    )

    assert result["allow_new_entries"] is True
    assert result["guard_status"] == "PASS"


def test_bear_market_blocks_new_entries():
    result = evaluate_mean_reversion_market_guard(
        {
            "status": "AVAILABLE",
            "regime": "BEAR",
        }
    )

    assert result["allow_new_entries"] is False
    assert result["guard_status"] == "BLOCKED"
    assert result["market_regime"] == "BEAR"


def test_unavailable_regime_blocks_new_entries():
    result = evaluate_mean_reversion_market_guard(
        {
            "status": "UNAVAILABLE",
            "regime": "",
        }
    )

    assert result["allow_new_entries"] is False
    assert result["guard_status"] == "BLOCKED"


def test_unknown_regime_blocks_new_entries():
    result = evaluate_mean_reversion_market_guard(
        {
            "status": "AVAILABLE",
            "regime": "UNKNOWN",
        }
    )

    assert result["allow_new_entries"] is False
    assert result["guard_status"] == "BLOCKED"


def test_missing_regime_result_blocks_new_entries():
    result = evaluate_mean_reversion_market_guard(
        None
    )

    assert result["allow_new_entries"] is False
    assert result["guard_status"] == "BLOCKED"


def test_guarded_queue_keeps_ready_in_bull_market():
    from strategies.mean_reversion_market_guard import (
        build_guarded_mean_reversion_queue_results,
    )

    raw_results = {
        "ready": [
            {
                "symbol": "TEST.TO",
                "decision": "READY",
            }
        ],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    result = (
        build_guarded_mean_reversion_queue_results(
            raw_results,
            {
                "status": "AVAILABLE",
                "regime": "BULL",
            },
        )
    )

    assert len(
        result["queue_results"]["ready"]
    ) == 1

    assert (
        result["blocked_ready_count"]
        == 0
    )

    assert (
        raw_results["ready"][0]["decision"]
        == "READY"
    )


def test_guarded_queue_blocks_ready_in_bear_market():
    from strategies.mean_reversion_market_guard import (
        build_guarded_mean_reversion_queue_results,
    )

    raw_results = {
        "ready": [
            {
                "symbol": "TEST.TO",
                "decision": "READY",
            }
        ],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    result = (
        build_guarded_mean_reversion_queue_results(
            raw_results,
            {
                "status": "AVAILABLE",
                "regime": "BEAR",
            },
        )
    )

    assert (
        result["queue_results"]["ready"]
        == []
    )

    assert (
        result["blocked_ready_count"]
        == 1
    )

    blocked = result[
        "queue_results"
    ]["watch"][0]

    assert (
        blocked["decision"]
        == "WATCH"
    )

    assert (
        blocked["raw_decision"]
        == "READY"
    )

    assert (
        blocked["market_regime"]
        == "BEAR"
    )

    assert (
        blocked["market_guard_status"]
        == "BLOCKED"
    )

    # Critical:
    # raw research result must remain unchanged.
    assert (
        raw_results["ready"][0]["decision"]
        == "READY"
    )


def test_unavailable_market_blocks_ready_queue():
    from strategies.mean_reversion_market_guard import (
        build_guarded_mean_reversion_queue_results,
    )

    raw_results = {
        "ready": [
            {
                "symbol": "TEST.TO",
                "decision": "READY",
            }
        ],
        "watch": [],
        "ignore": [],
        "errors": [],
    }

    result = (
        build_guarded_mean_reversion_queue_results(
            raw_results,
            {
                "status": "UNAVAILABLE",
                "regime": "",
            },
        )
    )

    assert (
        result["queue_results"]["ready"]
        == []
    )

    assert (
        result["blocked_ready_count"]
        == 1
    )
