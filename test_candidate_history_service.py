from pathlib import Path

import research.candidate_history_service as service


def test_capture_strategy_builds_and_saves_history(
    monkeypatch,
    tmp_path,
):
    journal = tmp_path / "journal.csv"

    snapshot = {
        "generated_at_utc": (
            "2026-08-14T18:00:00+00:00"
        ),
        "baseline": {
            "trade_count": 30,
        },
        "candidate_quality_gate": [],
    }

    captured = {}

    def fake_build_shadow_snapshot(
        journal_path,
    ):
        captured["journal_path"] = (
            journal_path
        )

        return snapshot

    def fake_append_candidate_history_record(
        received_snapshot,
        strategy_name,
        output_directory,
    ):
        captured["snapshot"] = (
            received_snapshot
        )
        captured["strategy_name"] = (
            strategy_name
        )
        captured["output_directory"] = (
            output_directory
        )

        return {
            "saved": True,
            "reason": "CHANGED",
            "path": (
                Path(output_directory)
                / "momentum.jsonl"
            ),
        }

    monkeypatch.setattr(
        service,
        "build_shadow_snapshot",
        fake_build_shadow_snapshot,
    )

    monkeypatch.setattr(
        service,
        "append_candidate_history_record",
        fake_append_candidate_history_record,
    )

    result = (
        service
        .capture_strategy_candidate_history(
            "Momentum",
            journal,
            output_directory=tmp_path,
        )
    )

    assert result["success"] is True
    assert result["saved"] is True
    assert result["reason"] == "CHANGED"

    assert (
        captured["journal_path"]
        == journal
    )

    assert (
        captured["snapshot"]
        is snapshot
    )

    assert (
        captured["strategy_name"]
        == "Momentum"
    )

    assert (
        captured["output_directory"]
        == tmp_path
    )


def test_capture_all_runs_three_strategies(
    monkeypatch,
    tmp_path,
):
    journals = {
        "Momentum": (
            tmp_path / "momentum.csv"
        ),
        "52-Week Breakout": (
            tmp_path / "breakout.csv"
        ),
        "Mean Reversion": (
            tmp_path / "mean_reversion.csv"
        ),
    }

    monkeypatch.setattr(
        service,
        "STRATEGY_JOURNALS",
        journals,
    )

    calls = []

    def fake_capture(
        strategy_name,
        journal_path,
        output_directory,
    ):
        calls.append(
            (
                strategy_name,
                journal_path,
                output_directory,
            )
        )

        return {
            "success": True,
            "strategy": strategy_name,
            "saved": True,
            "reason": "CHANGED",
            "path": str(
                tmp_path
                / (
                    strategy_name
                    + ".jsonl"
                )
            ),
        }

    monkeypatch.setattr(
        service,
        "capture_strategy_candidate_history",
        fake_capture,
    )

    result = (
        service
        .capture_all_candidate_history(
            output_directory=tmp_path
        )
    )

    assert result["success"] is True
    assert len(calls) == 3

    assert [
        call[0]
        for call in calls
    ] == [
        "Momentum",
        "52-Week Breakout",
        "Mean Reversion",
    ]


def test_one_strategy_failure_does_not_stop_others(
    monkeypatch,
    tmp_path,
):
    journals = {
        "Momentum": (
            tmp_path / "momentum.csv"
        ),
        "52-Week Breakout": (
            tmp_path / "breakout.csv"
        ),
        "Mean Reversion": (
            tmp_path / "mean_reversion.csv"
        ),
    }

    monkeypatch.setattr(
        service,
        "STRATEGY_JOURNALS",
        journals,
    )

    calls = []

    def fake_capture(
        strategy_name,
        journal_path,
        output_directory,
    ):
        calls.append(
            strategy_name
        )

        if (
            strategy_name
            == "52-Week Breakout"
        ):
            raise RuntimeError(
                "simulated research failure"
            )

        return {
            "success": True,
            "strategy": strategy_name,
            "saved": True,
            "reason": "CHANGED",
            "path": "test.jsonl",
        }

    monkeypatch.setattr(
        service,
        "capture_strategy_candidate_history",
        fake_capture,
    )

    result = (
        service
        .capture_all_candidate_history(
            output_directory=tmp_path
        )
    )

    assert result["success"] is False

    assert calls == [
        "Momentum",
        "52-Week Breakout",
        "Mean Reversion",
    ]

    assert (
        result["strategies"][
            "Momentum"
        ]["success"]
        is True
    )

    assert (
        result["strategies"][
            "52-Week Breakout"
        ]["success"]
        is False
    )

    assert (
        result["strategies"][
            "52-Week Breakout"
        ]["reason"]
        == "ERROR"
    )

    assert (
        result["strategies"][
            "Mean Reversion"
        ]["success"]
        is True
    )


def test_strategy_journals_are_independent():
    assert (
        service.STRATEGY_JOURNALS[
            "Momentum"
        ].name
        == "paper_trade_journal.csv"
    )

    assert (
        service.STRATEGY_JOURNALS[
            "52-Week Breakout"
        ].name
        == "paper_trade_journal_52week.csv"
    )

    assert (
        service.STRATEGY_JOURNALS[
            "Mean Reversion"
        ].name
        == "paper_trade_journal_mean_reversion.csv"
    )

    assert len(
        set(
            service
            .STRATEGY_JOURNALS
            .values()
        )
    ) == 3
