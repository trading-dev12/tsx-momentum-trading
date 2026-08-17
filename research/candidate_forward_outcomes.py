"""
Northstar Quant
Candidate Forward Outcome Research

Calculates post-signal outcomes for READY, WATCH and IGNORE
candidates.

Research only. This module never changes strategy decisions,
pending trades, positions, sizing, stops, targets or exits.
"""

from __future__ import annotations

import csv
from datetime import (
    date,
    datetime,
    timezone,
)
from pathlib import Path

import pandas as pd


FORWARD_OUTCOME_SCHEMA_VERSION = 1

HORIZONS = (
    1,
    2,
    3,
    5,
    10,
    20,
)

STRATEGY_DIRECTORIES = {
    "MOMENTUM": Path(
        "research/momentum_results"
    ),
    "52_WEEK_BREAKOUT": Path(
        "research/52_week_results"
    ),
    "MEAN_REVERSION": Path(
        "research/mean_reversion_results"
    ),
}

DEFAULT_OUTPUT_PATH = Path(
    "data/runtime/candidate_forward_outcomes.csv"
)


BASE_FIELDNAMES = [
    "schema_version",
    "updated_at_utc",
    "strategy",
    "signal_date",
    "symbol",
    "decision",
    "signal_price",
    "signal_tmqs",
    "signal_rvol",
    "signal_reason",
    "signal_data_source",
    "signal_price_source",
    "outcome_data_source",
    "historical_data_type",
    "as_of_date",
    "available_trading_days",
    "completed_horizon_count",
    "outcome_status",
    "outcome_error",
]


def _horizon_fieldnames():
    fields = []

    for horizon in HORIZONS:
        prefix = f"h{horizon}"

        fields.extend(
            [
                f"{prefix}_date",
                f"{prefix}_close",
                f"{prefix}_return_percent",
                (
                    f"{prefix}_max_high_"
                    "return_percent"
                ),
                (
                    f"{prefix}_min_low_"
                    "return_percent"
                ),
            ]
        )

    return fields


FIELDNAMES = (
    BASE_FIELDNAMES
    + _horizon_fieldnames()
)


def _text(value):
    return str(
        value
        if value is not None
        else ""
    ).strip()


def _number(
    value,
    default=None,
):
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    if result != result:
        return default

    return result


def _parse_date(value):
    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    return datetime.strptime(
        _text(value)[:10],
        "%Y-%m-%d",
    ).date()


def _candidate_key(row):
    return (
        _text(
            row.get("strategy")
        ).upper(),
        _text(
            row.get("signal_date")
        ),
        _text(
            row.get("symbol")
        ).upper(),
    )


def normalize_candidate_row(
    row,
    default_strategy="",
):
    """
    Normalize one strategy snapshot row into the common
    forward-outcome candidate format.
    """

    strategy = (
        _text(
            row.get("strategy")
        ).upper()
        or _text(
            default_strategy
        ).upper()
    )

    decision = _text(
        row.get("decision")
    ).upper()

    signal_price = _number(
        row.get(
            "close",
            row.get(
                "price"
            ),
        )
    )

    if signal_price is None:
        signal_price = _number(
            row.get("price")
        )

    return {
        "strategy": strategy,
        "signal_date": _text(
            row.get("signal_date")
        ),
        "symbol": _text(
            row.get("symbol")
        ).upper(),
        "decision": decision,
        "signal_price": signal_price,
        "signal_tmqs": _number(
            row.get("tmqs"),
            "",
        ),
        "signal_rvol": _number(
            row.get("rvol"),
            "",
        ),
        "signal_reason": _text(
            row.get("reason")
        ),
        "signal_data_source": (
            _text(
                row.get("data_source")
            )
            or _text(
                row.get(
                    "live_data_source"
                )
            )
            or _text(
                row.get(
                    "signal_quote_source"
                )
            )
        ),
        "signal_price_source": _text(
            row.get("price_source")
        ),
    }


def load_candidate_snapshot_rows(
    root_directory=".",
):
    """
    Load all persisted READY/WATCH/IGNORE candidate snapshots
    from the three strategy research directories.

    ERROR rows are intentionally excluded because they are
    failed observations rather than evaluated candidates.
    """

    root_directory = Path(
        root_directory
    )

    candidates = {}

    for (
        strategy,
        relative_directory,
    ) in STRATEGY_DIRECTORIES.items():
        directory = (
            root_directory
            / relative_directory
        )

        if not directory.exists():
            continue

        for path in sorted(
            directory.glob("*.csv")
        ):
            with path.open(
                "r",
                newline="",
                encoding="utf-8",
            ) as file:
                for row in csv.DictReader(
                    file
                ):
                    candidate = (
                        normalize_candidate_row(
                            row,
                            default_strategy=(
                                strategy
                            ),
                        )
                    )

                    if candidate[
                        "decision"
                    ] not in {
                        "READY",
                        "WATCH",
                        "IGNORE",
                    }:
                        continue

                    if not (
                        candidate["symbol"]
                        and candidate[
                            "signal_date"
                        ]
                    ):
                        continue

                    candidates[
                        _candidate_key(
                            candidate
                        )
                    ] = candidate

    return sorted(
        candidates.values(),
        key=lambda row: (
            row["signal_date"],
            row["strategy"],
            row["symbol"],
        ),
    )


def _prepare_history(
    history,
    as_of_date,
):
    if history is None:
        return pd.DataFrame()

    if not isinstance(
        history,
        pd.DataFrame,
    ):
        raise TypeError(
            "Historical data must be a pandas DataFrame."
        )

    required = {
        "date",
        "high",
        "low",
        "close",
    }

    missing = (
        required
        - set(history.columns)
    )

    if missing:
        raise ValueError(
            "Historical data missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    frame = history.copy()

    frame["date"] = pd.to_datetime(
        frame["date"],
        errors="coerce",
    )

    for field in (
        "high",
        "low",
        "close",
    ):
        frame[field] = pd.to_numeric(
            frame[field],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "date",
            "high",
            "low",
            "close",
        ]
    )

    frame = frame.sort_values(
        "date"
    )

    frame = frame.drop_duplicates(
        subset=["date"],
        keep="last",
    )

    cutoff = pd.Timestamp(
        as_of_date
    ).normalize()

    frame = frame[
        frame["date"].dt.normalize()
        <= cutoff
    ].copy()

    return frame.reset_index(
        drop=True
    )


def calculate_candidate_forward_outcomes(
    candidate,
    history,
    as_of_date=None,
    captured_at=None,
):
    """
    Calculate forward outcomes from the signal price.

    Horizon +N means the Nth actual trading bar after the
    signal date. Weekends and market holidays therefore do not
    consume horizon days because no bar exists for them.

    max_high_return_percent and min_low_return_percent measure
    the most favorable and most adverse price excursion reached
    from the signal price through that horizon.
    """

    if as_of_date is None:
        as_of_date = datetime.now(
            timezone.utc
        ).date()

    as_of_date = _parse_date(
        as_of_date
    )

    if captured_at is None:
        updated_at = datetime.now(
            timezone.utc
        ).isoformat()
    elif isinstance(
        captured_at,
        datetime,
    ):
        if (
            captured_at.tzinfo
            is None
        ):
            captured_at = (
                captured_at.replace(
                    tzinfo=timezone.utc
                )
            )

        updated_at = (
            captured_at
            .astimezone(
                timezone.utc
            )
            .isoformat()
        )
    else:
        updated_at = _text(
            captured_at
        )

    normalized = (
        normalize_candidate_row(
            candidate,
            default_strategy=(
                candidate.get(
                    "strategy",
                    "",
                )
            ),
        )
    )

    row = {
        field: ""
        for field in FIELDNAMES
    }

    row.update(
        {
            "schema_version": (
                FORWARD_OUTCOME_SCHEMA_VERSION
            ),
            "updated_at_utc": (
                updated_at
            ),
            **normalized,
            "as_of_date": (
                as_of_date.isoformat()
            ),
            "available_trading_days": 0,
            "completed_horizon_count": 0,
            "outcome_status": "PENDING",
            "outcome_error": "",
        }
    )

    try:
        signal_date = _parse_date(
            normalized[
                "signal_date"
            ]
        )

        signal_price = _number(
            normalized[
                "signal_price"
            ]
        )

        if (
            signal_price is None
            or signal_price <= 0
        ):
            raise ValueError(
                "Candidate signal price is unavailable."
            )

        frame = _prepare_history(
            history,
            as_of_date=as_of_date,
        )

        row[
            "outcome_data_source"
        ] = _text(
            getattr(
                frame,
                "attrs",
                {},
            ).get(
                "data_source",
                getattr(
                    history,
                    "attrs",
                    {},
                ).get(
                    "data_source",
                    "",
                ),
            )
        )

        row[
            "historical_data_type"
        ] = _text(
            getattr(
                frame,
                "attrs",
                {},
            ).get(
                "historical_data_type",
                getattr(
                    history,
                    "attrs",
                    {},
                ).get(
                    "historical_data_type",
                    "",
                ),
            )
        )

        future = frame[
            frame["date"].dt.date
            > signal_date
        ].copy()

        future = future.reset_index(
            drop=True
        )

        row[
            "available_trading_days"
        ] = len(future)

        completed = 0

        for horizon in HORIZONS:
            if len(future) < horizon:
                continue

            prefix = f"h{horizon}"

            horizon_row = future.iloc[
                horizon - 1
            ]

            path = future.iloc[
                :horizon
            ]

            close_price = float(
                horizon_row[
                    "close"
                ]
            )

            max_high = float(
                path["high"].max()
            )

            min_low = float(
                path["low"].min()
            )

            row[
                f"{prefix}_date"
            ] = (
                horizon_row["date"]
                .date()
                .isoformat()
            )

            row[
                f"{prefix}_close"
            ] = round(
                close_price,
                6,
            )

            row[
                f"{prefix}_return_percent"
            ] = round(
                (
                    (
                        close_price
                        / signal_price
                    )
                    - 1
                )
                * 100,
                6,
            )

            row[
                (
                    f"{prefix}_max_high_"
                    "return_percent"
                )
            ] = round(
                (
                    (
                        max_high
                        / signal_price
                    )
                    - 1
                )
                * 100,
                6,
            )

            row[
                (
                    f"{prefix}_min_low_"
                    "return_percent"
                )
            ] = round(
                (
                    (
                        min_low
                        / signal_price
                    )
                    - 1
                )
                * 100,
                6,
            )

            completed += 1

        row[
            "completed_horizon_count"
        ] = completed

        if completed == len(
            HORIZONS
        ):
            row[
                "outcome_status"
            ] = "COMPLETE"

        elif completed > 0:
            row[
                "outcome_status"
            ] = "PARTIAL"

        else:
            row[
                "outcome_status"
            ] = "PENDING"

    except Exception as error:
        row[
            "outcome_status"
        ] = "ERROR"

        row[
            "outcome_error"
        ] = str(error)

    return row


def save_candidate_forward_outcomes(
    rows,
    output_path=DEFAULT_OUTPUT_PATH,
):
    """
    Atomically save the forward-outcome table.
    """

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = Path(
        str(output_path)
        + ".tmp"
    )

    with temporary_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
        )

        writer.writeheader()

        writer.writerows(
            sorted(
                rows,
                key=lambda row: (
                    _text(
                        row.get(
                            "signal_date"
                        )
                    ),
                    _text(
                        row.get(
                            "strategy"
                        )
                    ),
                    _text(
                        row.get(
                            "symbol"
                        )
                    ),
                ),
            )
        )

    temporary_path.replace(
        output_path
    )

    return {
        "success": True,
        "status": "SAVED",
        "output_path": str(
            output_path
        ),
        "rows_saved": len(rows),
    }
