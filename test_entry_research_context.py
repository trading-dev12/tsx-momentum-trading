import csv

from paper_trading.paper_engine import (
    PaperTradingEngine,
)
from research.entry_context import (
    build_entry_context,
    build_runtime_fingerprint,
)


class FakePortfolio:
    def summary(self):
        return {
            "cash": 450000.0,
            "portfolio_value": 500000.0,
            "open_position_value": 50000.0,
            "portfolio_exposure": 10.0,
            "open_positions": 4,
            "closed_trades": 27,
        }


def test_build_entry_context_keeps_portfolio_and_risk_state():
    context = build_entry_context(
        portfolio=FakePortfolio(),
        sizing_diagnostics={
            "risk_model": "fixed",
            "risk_budget": 100.0,
            "maximum_position_value": 100000.0,
            "limiting_factor": "risk",
            "decision": "ACCEPTED",
        },
        entry_price=102.0,
        stop_price=100.0,
        target_price=107.0,
        shares=50,
        atr_multiplier=2.0,
        reward_multiplier=2.5,
        max_hold_days=10,
        signal_close=100.0,
    )

    assert (
        context["entry_context_status"]
        == "AVAILABLE"
    )

    assert (
        context["entry_cash_before"]
        == 450000.0
    )

    assert (
        context["entry_portfolio_value_before"]
        == 500000.0
    )

    assert (
        context["entry_open_positions_before"]
        == 4
    )

    assert (
        context["entry_position_value"]
        == 5100.0
    )

    assert (
        context["entry_initial_risk_per_share"]
        == 2.0
    )

    assert (
        context["entry_initial_risk_amount"]
        == 100.0
    )

    assert (
        context["entry_risk_budget"]
        == 100.0
    )

    assert (
        context["entry_sizing_limiting_factor"]
        == "risk"
    )

    assert (
        context["entry_atr_multiplier"]
        == 2.0
    )

    assert (
        context["entry_reward_multiplier"]
        == 2.5
    )

    assert (
        context["entry_max_hold_days"]
        == 10
    )

    assert (
        context["signal_to_entry_gap_percent"]
        == 2.0
    )


def test_runtime_fingerprint_is_populated():
    fingerprint = (
        build_runtime_fingerprint()
    )

    assert len(
        fingerprint[
            "entry_config_sha256"
        ]
    ) == 64

    assert len(
        fingerprint[
            "entry_strategy_code_sha256"
        ]
    ) == 64

    assert (
        fingerprint[
            "entry_config_snapshot_json"
        ]
    )

    assert (
        fingerprint[
            "entry_project_version"
        ]
        == "1.0"
    )

    assert fingerprint[
        "entry_fingerprint_status"
    ] in {
        "AVAILABLE",
        "PARTIAL",
    }


def build_engine(
    tmp_path,
):
    return PaperTradingEngine(
        starting_cash=500000,
        portfolio_state_file=(
            tmp_path
            / "portfolio.json"
        ),
        pending_trades_file=(
            tmp_path
            / "pending.csv"
        ),
        journal_file=(
            tmp_path
            / "journal.csv"
        ),
        risk_model="fixed",
        fixed_risk_amount=100.0,
        max_open_positions=100,
    )


def test_pending_execution_context_survives_to_completed_journal(
    tmp_path,
    monkeypatch,
):
    engine = build_engine(
        tmp_path
    )

    monkeypatch.setattr(
        "paper_trading.paper_engine.enrich_trade",
        lambda position: {},
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_opened",
        lambda position: None,
    )

    monkeypatch.setattr(
        engine,
        "_notify_trade_closed",
        lambda trade: None,
    )

    monkeypatch.setattr(
        "paper_trading.paper_engine.capture_trade_path",
        lambda trade: {
            "trade_path_status": "NO_DATA",
            "trade_path_source": (
                "IBKR_ONE_MINUTE"
            ),
            "trade_path_bar_count": 0,
            "trade_path_bars_saved": 0,
        },
    )

    signal = {
        "symbol": "TEST.TO",
        "strategy": "MOMENTUM",
        "signal_date": "2026-08-17",
        "close": 100.0,
        "atr": 1.0,
        "tmqs": 90.0,
        "rvol": 2.0,
        "breakout": "BREAKOUT",
        "reason": "Research test",
        "decision": "READY",
    }

    queued = engine.queue_signal(
        signal
    )

    assert queued["success"] is True

    opened = (
        engine.execute_pending_trade(
            symbol="TEST.TO",
            entry_price=102.0,
            entry_date="2026-08-18",
            price_source=(
                "IBKR_ONE_MINUTE_OPEN"
            ),
            atr_multiplier=2.0,
            reward_multiplier=2.5,
            max_hold_days=10,
        )
    )

    assert opened["success"] is True

    assert len(
        engine.portfolio.open_positions
    ) == 1

    position = (
        engine.portfolio.open_positions[
            0
        ]
    )

    assert (
        position["entry_context_status"]
        == "AVAILABLE"
    )

    assert (
        position["entry_initial_risk_amount"]
        == 100.0
    )

    assert (
        position["signal_to_entry_gap_percent"]
        == 2.0
    )

    assert (
        position["entry_risk_model"]
        == "fixed"
    )

    assert position[
        "entry_git_commit"
    ]

    result = engine.close_position(
        symbol="TEST.TO",
        exit_price=103.0,
        current_date="2026-08-18",
    )

    assert result["success"] is True

    with (
        tmp_path
        / "journal.csv"
    ).open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(
            csv.DictReader(file)
        )

    assert len(rows) == 1

    row = rows[0]

    assert (
        row["entry_context_status"]
        == "AVAILABLE"
    )

    assert (
        row["entry_initial_risk_amount"]
        == "100.0"
    )

    assert (
        row["entry_atr_multiplier"]
        == "2.0"
    )

    assert (
        row["entry_reward_multiplier"]
        == "2.5"
    )

    assert (
        row["entry_max_hold_days"]
        == "10"
    )

    assert (
        row["signal_to_entry_gap_percent"]
        == "2.0"
    )

    assert row[
        "entry_git_commit"
    ]

    assert len(
        row[
            "entry_strategy_code_sha256"
        ]
    ) == 64
