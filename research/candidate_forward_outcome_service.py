"""
Northstar Quant
Candidate Forward Outcome Refresh Service

Matures previously captured READY/WATCH/IGNORE candidate
outcomes using IBKR historical daily bars.

Research only. This service never changes strategy decisions,
queues, positions, portfolios, sizing or execution.
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

from core.ibkr_data_provider import (
    IBKRDataProvider,
)
from research.candidate_forward_outcomes import (
    DEFAULT_OUTPUT_PATH,
    calculate_candidate_forward_outcomes,
    load_candidate_snapshot_rows,
    save_candidate_forward_outcomes,
)
from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


FORWARD_OUTCOME_IBKR_CLIENT_ID = 20

DEFAULT_MAX_SYMBOLS_PER_RUN = 20

DEFAULT_HISTORY_DURATION = "2 Y"


def _text(value):
    return str(
        value
        if value is not None
        else ""
    ).strip()


def _key(row):
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


def _date_text(value):
    if isinstance(
        value,
        datetime,
    ):
        return value.date().isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    return _text(value)[:10]


def load_existing_forward_outcomes(
    output_path=DEFAULT_OUTPUT_PATH,
):
    """
    Load the current forward-outcome table keyed by
    strategy + signal date + symbol.
    """

    output_path = Path(
        output_path
    )

    if not output_path.exists():
        return {}

    rows = {}

    with output_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        for row in csv.DictReader(
            file
        ):
            key = _key(row)

            if all(key):
                rows[key] = row

    return rows


def _empty_history():
    return pd.DataFrame(
        columns=[
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    )


def _candidate_is_older_than_as_of(
    candidate,
    as_of_date,
):
    try:
        signal_date = datetime.strptime(
            _date_text(
                candidate.get(
                    "signal_date"
                )
            ),
            "%Y-%m-%d",
        ).date()

        comparison_date = datetime.strptime(
            _date_text(
                as_of_date
            ),
            "%Y-%m-%d",
        ).date()

        return (
            signal_date
            < comparison_date
        )

    except (
        TypeError,
        ValueError,
    ):
        # Let the outcome calculator record the malformed
        # observation rather than silently dropping it.
        return True


def _oldest_signal_date(
    candidates,
):
    dates = [
        _date_text(
            candidate.get(
                "signal_date"
            )
        )
        for candidate in candidates
    ]

    dates = [
        value
        for value in dates
        if value
    ]

    return (
        min(dates)
        if dates
        else "9999-12-31"
    )


def run_candidate_forward_outcome_refresh(
    as_of_date=None,
    root_directory=".",
    output_path=DEFAULT_OUTPUT_PATH,
    max_symbols_per_run=(
        DEFAULT_MAX_SYMBOLS_PER_RUN
    ),
    history_duration=(
        DEFAULT_HISTORY_DURATION
    ),
    candidate_loader=(
        load_candidate_snapshot_rows
    ),
    history_loader=(
        load_ibkr_daily_history
    ),
    provider=None,
    provider_factory=IBKRDataProvider,
    captured_at=None,
):
    """
    Mature incomplete candidate outcomes.

    Efficiency / pacing rules:
    - COMPLETE candidates are never requested again.
    - candidates from the as-of date do not need history yet.
    - all incomplete candidates for one symbol share one
      historical-data request.
    - only a bounded number of symbols are refreshed per run.
    - oldest incomplete symbols receive priority.

    A later refresh can reconstruct missed horizons, so delayed
    refreshes do not lose research information.
    """

    if as_of_date is None:
        as_of_date = datetime.now(
            timezone.utc
        ).date()

    as_of_text = _date_text(
        as_of_date
    )

    if captured_at is None:
        captured_at = datetime.now(
            timezone.utc
        )

    try:
        max_symbols_per_run = max(
            0,
            int(
                max_symbols_per_run
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        max_symbols_per_run = (
            DEFAULT_MAX_SYMBOLS_PER_RUN
        )

    candidates = candidate_loader(
        root_directory=root_directory
    )

    existing = (
        load_existing_forward_outcomes(
            output_path=output_path
        )
    )

    outcomes = dict(
        existing
    )

    empty_history = _empty_history()

    incomplete_by_symbol = {}

    complete_preserved = 0

    same_day_pending = 0

    for candidate in candidates:
        key = _key(
            candidate
        )

        existing_row = existing.get(
            key
        )

        if existing_row is None:
            # Ensure every candidate appears in the durable
            # output even before its first IBKR refresh.
            outcomes[key] = (
                calculate_candidate_forward_outcomes(
                    candidate,
                    empty_history,
                    as_of_date=as_of_text,
                    captured_at=captured_at,
                )
            )

        elif (
            _text(
                existing_row.get(
                    "outcome_status"
                )
            ).upper()
            == "COMPLETE"
        ):
            complete_preserved += 1
            continue

        if not _candidate_is_older_than_as_of(
            candidate,
            as_of_text,
        ):
            same_day_pending += 1
            continue

        symbol = _text(
            candidate.get("symbol")
        ).upper()

        if not symbol:
            continue

        incomplete_by_symbol.setdefault(
            symbol,
            [],
        ).append(
            candidate
        )

    eligible_symbols = sorted(
        incomplete_by_symbol,
        key=lambda symbol: (
            _oldest_signal_date(
                incomplete_by_symbol[
                    symbol
                ]
            ),
            symbol,
        ),
    )

    selected_symbols = (
        eligible_symbols[
            :max_symbols_per_run
        ]
    )

    deferred_symbols = (
        eligible_symbols[
            max_symbols_per_run:
        ]
    )

    owns_provider = False

    if (
        selected_symbols
        and provider is None
    ):
        provider = provider_factory(
            client_id=(
                FORWARD_OUTCOME_IBKR_CLIENT_ID
            )
        )

        owns_provider = True

    symbol_errors = {}

    refreshed_candidates = 0

    try:
        for symbol in selected_symbols:
            symbol_candidates = (
                incomplete_by_symbol[
                    symbol
                ]
            )

            try:
                history = history_loader(
                    symbol=symbol,
                    measurement_date=(
                        as_of_text
                    ),
                    duration=(
                        history_duration
                    ),
                    adjusted=False,
                    provider=provider,
                )

            except Exception as error:
                error_text = str(
                    error
                )

                symbol_errors[
                    symbol
                ] = error_text

                # Never destroy previously captured partial
                # outcomes because of a temporary IBKR failure.
                # A brand-new row can record the failure and
                # will be retried on a later refresh.
                for candidate in (
                    symbol_candidates
                ):
                    key = _key(
                        candidate
                    )

                    if key in existing:
                        continue

                    error_row = dict(
                        outcomes[
                            key
                        ]
                    )

                    error_row[
                        "outcome_status"
                    ] = "ERROR"

                    error_row[
                        "outcome_error"
                    ] = error_text

                    outcomes[
                        key
                    ] = error_row

                continue

            for candidate in (
                symbol_candidates
            ):
                row = (
                    calculate_candidate_forward_outcomes(
                        candidate,
                        history,
                        as_of_date=(
                            as_of_text
                        ),
                        captured_at=(
                            captured_at
                        ),
                    )
                )

                outcomes[
                    _key(candidate)
                ] = row

                refreshed_candidates += 1

    finally:
        if owns_provider:
            disconnect = getattr(
                provider,
                "disconnect",
                None,
            )

            if callable(
                disconnect
            ):
                disconnect()

    saved_rows = list(
        outcomes.values()
    )

    save_result = (
        save_candidate_forward_outcomes(
            saved_rows,
            output_path=output_path,
        )
    )

    current_rows = [
        outcomes[
            _key(candidate)
        ]
        for candidate in candidates
        if _key(candidate)
        in outcomes
    ]

    status_counts = {}

    for row in current_rows:
        status = (
            _text(
                row.get(
                    "outcome_status"
                )
            ).upper()
            or "UNKNOWN"
        )

        status_counts[
            status
        ] = (
            status_counts.get(
                status,
                0,
            )
            + 1
        )

    if not candidates:
        status = "NO_CANDIDATES"

    elif (
        symbol_errors
        or deferred_symbols
    ):
        status = "PARTIAL"

    else:
        status = "UPDATED"

    return {
        "success": (
            len(symbol_errors)
            == 0
        ),
        "status": status,
        "as_of_date": as_of_text,
        "candidates_loaded": len(
            candidates
        ),
        "rows_saved": (
            save_result[
                "rows_saved"
            ]
        ),
        "complete_preserved": (
            complete_preserved
        ),
        "same_day_pending": (
            same_day_pending
        ),
        "eligible_symbols": len(
            eligible_symbols
        ),
        "symbols_requested": len(
            selected_symbols
        ),
        "symbols_deferred": len(
            deferred_symbols
        ),
        "refreshed_candidates": (
            refreshed_candidates
        ),
        "symbol_errors": (
            symbol_errors
        ),
        "status_counts": (
            status_counts
        ),
        "output_path": str(
            output_path
        ),
    }
