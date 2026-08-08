import json

from research.shadow_edge_analyzer import (
    CATEGORICAL_FACTORS,
    NUMERIC_FACTORS,
)
from research.shadow_edge_snapshot import (
    build_shadow_snapshot,
    save_shadow_snapshot,
)


def _write_test_journal(path):
    fieldnames = [
        "profit_loss",
        "profit_loss_percent",
        "entry_date",
        "exit_date",
        *CATEGORICAL_FACTORS,
        *NUMERIC_FACTORS,
    ]

    rows = []

    for index in range(6):
        row = {
            "profit_loss": (
                "100"
                if index < 3
                else "-100"
            ),
            "profit_loss_percent": (
                "1"
                if index < 3
                else "-1"
            ),
            "entry_date": (
                f"2026-07-{10 + index:02d}"
            ),
            "exit_date": (
                f"2026-07-{11 + index:02d}"
            ),
        }

        for factor in CATEGORICAL_FACTORS:
            row[factor] = (
                "GOOD"
                if index < 3
                else "BAD"
            )

        for factor in NUMERIC_FACTORS:
            row[factor] = str(
                index + 1
            )

        rows.append(row)

    import csv

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def test_shadow_snapshot_builds_research_sections(
    tmp_path,
):
    journal = (
        tmp_path
        / "journal.csv"
    )

    _write_test_journal(
        journal
    )

    snapshot = build_shadow_snapshot(
        journal
    )

    assert (
        snapshot["snapshot_version"]
        == 1
    )

    assert (
        snapshot["baseline"][
            "trade_count"
        ]
        == 6
    )

    assert (
        "candidate_quality_gate"
        in snapshot
    )

    assert (
        "combination_readiness"
        in snapshot
    )

    assert (
        snapshot[
            "combination_readiness"
        ]["status"]
        == "NOT_READY"
    )


def test_shadow_snapshot_saves_valid_json(
    tmp_path,
):
    journal = (
        tmp_path
        / "journal.csv"
    )

    output_directory = (
        tmp_path
        / "snapshots"
    )

    _write_test_journal(
        journal
    )

    output_path = (
        save_shadow_snapshot(
            journal,
            output_directory=(
                output_directory
            ),
        )
    )

    assert output_path.exists()

    saved = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert (
        saved["snapshot_version"]
        == 1
    )

    assert (
        saved["baseline"][
            "trade_count"
        ]
        == 6
    )
