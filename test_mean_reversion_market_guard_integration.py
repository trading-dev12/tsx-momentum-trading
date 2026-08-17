import paper_trading.automatic_eod as automatic_eod


def make_raw_results():
    return {
        "ready": [
            {
                "symbol": "TEST.TO",
                "strategy": "MEAN_REVERSION",
                "signal_date": "2026-08-13",
                "close": 100.0,
                "atr": 2.0,
                "tmqs": 0.0,
                "rvol": 0.0,
                "breakout": "NO_BREAKOUT",
                "decision": "READY",
                "reason": "Test Mean Reversion READY",
            }
        ],
        "watch": [],
        "ignore": [],
        "errors": [],
    }


class FakePendingTrades:
    def get_all(self):
        return []


class FakePaperEngine:
    def __init__(self):
        self.pending_trades = FakePendingTrades()
        self.received_results = None

    def queue_eod_signals(
        self,
        results,
    ):
        self.received_results = results

        added = len(
            results["ready"]
        )

        return {
            "attempted": added,
            "added": added,
            "rejected": 0,
            "already_open": 0,
            "already_pending": 0,
            "other_rejected": 0,
            "results": [],
        }


def prepare_scan(
    monkeypatch,
    raw_results,
):
    monkeypatch.setattr(
        automatic_eod,
        "load_all_watchlists",
        lambda: ["TEST.TO"],
    )

    monkeypatch.setattr(
        automatic_eod,
        "scan_mean_reversion",
        lambda watchlist, measurement_date=None: raw_results,
    )

    saved_results = []

    def fake_save(
        results,
        measurement_date=None,
    ):
        saved_results.append(
            results
        )

        return "test_mean_reversion.csv"

    monkeypatch.setattr(
        automatic_eod,
        "save_mean_reversion_results",
        fake_save,
    )

    return saved_results


def test_bear_market_blocks_mean_reversion_queue(
    monkeypatch,
):
    raw_results = make_raw_results()

    saved_results = prepare_scan(
        monkeypatch,
        raw_results,
    )

    engine = FakePaperEngine()

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=engine,
            measurement_date="2026-08-13",
            market_regime_provider=lambda date: {
                "status": "AVAILABLE",
                "regime": "BEAR",
            },
        )
    )

    # Raw research signal still exists.
    assert result["ready"] == 1

    assert (
        raw_results["ready"][0]["decision"]
        == "READY"
    )

    # Raw results were saved before guard filtering.
    assert saved_results[0] is raw_results

    # But nothing reached the executable READY queue.
    assert result["queue_ready"] == 0

    assert (
        result["market_guard_blocked"]
        == 1
    )

    assert result["queued"] == 0

    assert (
        engine.received_results["ready"]
        == []
    )

    blocked = (
        engine
        .received_results["watch"][0]
    )

    assert (
        blocked["raw_decision"]
        == "READY"
    )

    assert (
        blocked["decision"]
        == "WATCH"
    )

    assert (
        blocked["market_regime"]
        == "BEAR"
    )


def test_bull_market_allows_mean_reversion_queue(
    monkeypatch,
):
    raw_results = make_raw_results()

    prepare_scan(
        monkeypatch,
        raw_results,
    )

    engine = FakePaperEngine()

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=engine,
            measurement_date="2026-08-13",
            market_regime_provider=lambda date: {
                "status": "AVAILABLE",
                "regime": "BULL",
            },
        )
    )

    assert result["ready"] == 1

    assert result["queue_ready"] == 1

    assert (
        result["market_guard_blocked"]
        == 0
    )

    assert result["queued"] == 1

    assert len(
        engine.received_results["ready"]
    ) == 1

    assert (
        engine
        .received_results["ready"][0]
        ["symbol"]
        == "TEST.TO"
    )


def test_unavailable_market_regime_blocks_queue(
    monkeypatch,
):
    raw_results = make_raw_results()

    prepare_scan(
        monkeypatch,
        raw_results,
    )

    engine = FakePaperEngine()

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=engine,
            measurement_date="2026-08-13",
            market_regime_provider=lambda date: {
                "status": "UNAVAILABLE",
                "regime": "",
                "reason": "Test unavailable",
            },
        )
    )

    # Research signal is preserved.
    assert result["ready"] == 1

    assert (
        raw_results["ready"][0]["decision"]
        == "READY"
    )

    # Trading entry is blocked.
    assert result["queue_ready"] == 0
    assert result["queued"] == 0

    assert (
        result["market_guard_blocked"]
        == 1
    )

    assert (
        result["market_guard"]["guard_status"]
        == "BLOCKED"
    )

    assert (
        engine.received_results["ready"]
        == []
    )


def test_market_regime_provider_error_blocks_queue(
    monkeypatch,
):
    raw_results = make_raw_results()

    prepare_scan(
        monkeypatch,
        raw_results,
    )

    engine = FakePaperEngine()

    def broken_regime_provider(date):
        raise RuntimeError(
            "Simulated XIC regime failure"
        )

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=engine,
            measurement_date="2026-08-13",
            market_regime_provider=(
                broken_regime_provider
            ),
        )
    )

    assert result["ready"] == 1

    assert result["queue_ready"] == 0
    assert result["queued"] == 0

    assert (
        result["market_guard_blocked"]
        == 1
    )

    assert (
        result["market_guard"]["guard_status"]
        == "BLOCKED"
    )

    assert (
        engine.received_results["ready"]
        == []
    )


def test_scan_without_paper_engine_does_not_call_regime_provider(
    monkeypatch,
):
    raw_results = make_raw_results()

    prepare_scan(
        monkeypatch,
        raw_results,
    )

    def forbidden_regime_provider(date):
        raise AssertionError(
            "Market regime provider must not be called "
            "during research-only scanner refresh."
        )

    result = (
        automatic_eod
        .run_mean_reversion_shadow_scan(
            paper_engine=None,
            measurement_date="2026-08-13",
            market_regime_provider=(
                forbidden_regime_provider
            ),
        )
    )

    assert result["ready"] == 1
    assert result["queued"] == 0

    assert (
        result["market_guard"]["guard_status"]
        == "NOT_EVALUATED"
    )

    assert (
        raw_results["ready"][0]["decision"]
        == "READY"
    )
