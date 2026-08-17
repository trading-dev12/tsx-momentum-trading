"""
Northstar Quant
Research Enrichment Integrity Monitor

Read-only validation of completed-trade research enrichment.

Historical trades may predate the current enrichment pipeline.
Trades entered on or after the monitoring start date are expected
to contain every research factor required by the Shadow Edge Analyzer.

This module never changes strategy rules, trades, journals,
positions, portfolios, or pending trades.
"""

from datetime import date

from research.shadow_edge_analyzer import (
    CATEGORICAL_FACTORS,
    NUMERIC_FACTORS,
    load_completed_trades,
)


ENRICHMENT_MONITOR_START_DATE = date(
    2026,
    8,
    10,
)


def _parse_entry_date(value):
    """
    Convert an ISO entry date into a date object.
    """

    text = str(
        value or ""
    ).strip()

    if not text:
        return None

    try:
        return date.fromisoformat(
            text
        )
    except ValueError:
        return None


def missing_enrichment_fields(trade):
    """
    Return fields preventing one trade from being fully enriched.

    This deliberately mirrors the Shadow Edge Analyzer definition.
    """

    missing = []

    for factor in CATEGORICAL_FACTORS:
        value = trade.get(
            factor,
            "",
        )

        if (
            value is None
            or not str(value).strip()
        ):
            missing.append(
                factor
            )

    for factor in NUMERIC_FACTORS:
        value = trade.get(
            factor,
            "",
        )

        if value is None:
            missing.append(
                factor
            )
            continue

        text = str(
            value
        ).strip()

        if not text:
            missing.append(
                factor
            )
            continue

        try:
            float(text)
        except (TypeError, ValueError):
            missing.append(
                factor
            )

    return missing


def analyze_enrichment_integrity(
    trades,
    monitor_start_date=(
        ENRICHMENT_MONITOR_START_DATE
    ),
):
    """
    Measure overall enrichment and integrity of newly entered trades.
    """

    total_trade_count = len(
        trades
    )

    fully_enriched_trade_count = 0
    legacy_trade_count = 0
    monitored_trade_count = 0
    monitored_fully_enriched_count = 0
    monitored_incomplete_count = 0
    undated_trade_count = 0

    missing_factor_counts = {
        factor: 0
        for factor in (
            list(CATEGORICAL_FACTORS)
            + list(NUMERIC_FACTORS)
        )
    }

    incomplete_monitored_trades = []

    for trade in trades:
        missing_fields = (
            missing_enrichment_fields(
                trade
            )
        )

        if not missing_fields:
            fully_enriched_trade_count += 1

        entry_date = _parse_entry_date(
            trade.get(
                "entry_date",
                "",
            )
        )

        if entry_date is None:
            undated_trade_count += 1
            continue

        if entry_date < monitor_start_date:
            legacy_trade_count += 1
            continue

        monitored_trade_count += 1

        if not missing_fields:
            monitored_fully_enriched_count += 1
            continue

        monitored_incomplete_count += 1

        for factor in missing_fields:
            missing_factor_counts[
                factor
            ] += 1

        incomplete_monitored_trades.append(
            {
                "symbol": str(
                    trade.get(
                        "symbol",
                        "--",
                    )
                ),
                "entry_date": (
                    entry_date.isoformat()
                ),
                "missing_fields": (
                    list(
                        missing_fields
                    )
                ),
            }
        )

    not_fully_enriched_trade_count = (
        total_trade_count
        - fully_enriched_trade_count
    )

    if monitored_trade_count == 0:
        integrity_status = (
            "NO_MONITORED_TRADES_YET"
        )
    elif monitored_incomplete_count:
        integrity_status = "FAIL"
    else:
        integrity_status = "PASS"

    if total_trade_count:
        overall_coverage_percent = (
            fully_enriched_trade_count
            / total_trade_count
            * 100.0
        )
    else:
        overall_coverage_percent = 0.0

    if monitored_trade_count:
        monitored_coverage_percent = (
            monitored_fully_enriched_count
            / monitored_trade_count
            * 100.0
        )
    else:
        monitored_coverage_percent = 0.0

    return {
        "integrity_status": (
            integrity_status
        ),
        "monitor_start_date": (
            monitor_start_date.isoformat()
        ),
        "total_trade_count": (
            total_trade_count
        ),
        "fully_enriched_trade_count": (
            fully_enriched_trade_count
        ),
        "not_fully_enriched_trade_count": (
            not_fully_enriched_trade_count
        ),
        "overall_coverage_percent": (
            overall_coverage_percent
        ),
        "legacy_trade_count": (
            legacy_trade_count
        ),
        "undated_trade_count": (
            undated_trade_count
        ),
        "monitored_trade_count": (
            monitored_trade_count
        ),
        "monitored_fully_enriched_count": (
            monitored_fully_enriched_count
        ),
        "monitored_incomplete_count": (
            monitored_incomplete_count
        ),
        "monitored_coverage_percent": (
            monitored_coverage_percent
        ),
        "missing_factor_counts": (
            missing_factor_counts
        ),
        "incomplete_monitored_trades": (
            incomplete_monitored_trades
        ),
    }


def analyze_enrichment_integrity_journal(
    file_path,
    monitor_start_date=(
        ENRICHMENT_MONITOR_START_DATE
    ),
):
    """
    Analyze one completed paper-trade journal read-only.
    """

    trades = load_completed_trades(
        file_path
    )

    return analyze_enrichment_integrity(
        trades,
        monitor_start_date=(
            monitor_start_date
        ),
    )

# ============================================================
# 200-Trade Research Capture Integrity
# ============================================================

CAPTURE_MONITOR_START_DATE = date(
    2026,
    8,
    18,
)


CAPTURE_GROUP_NAMES = [
    "signal_snapshot",
    "entry_context",
    "entry_fingerprint",
    "entry_quote",
    "exit_quote",
    "trade_path",
]


def _capture_text(value):
    """
    True when a research field contains usable text.
    """

    return bool(
        str(
            value or ""
        ).strip()
    )


def _capture_number(
    value,
    minimum=None,
    strictly_positive=False,
):
    """
    Validate a numeric research value.

    Zero is valid for fields such as portfolio exposure,
    prior closed-trade count and spread amount.
    """

    if value is None:
        return False

    text = str(
        value
    ).strip()

    if not text:
        return False

    try:
        number = float(
            text
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    if strictly_positive:
        return number > 0

    if minimum is not None:
        return number >= minimum

    return True


def _capture_json_object(value):
    """
    Validate a stored JSON research snapshot.
    """

    import json

    text = str(
        value or ""
    ).strip()

    if not text:
        return False

    try:
        result = json.loads(
            text
        )
    except (
        TypeError,
        ValueError,
    ):
        return False

    return isinstance(
        result,
        dict,
    )


def _capture_hex_digest(
    value,
    length,
):
    """
    Validate a Git/SHA research fingerprint.
    """

    text = str(
        value or ""
    ).strip().lower()

    if len(text) != length:
        return False

    return all(
        character
        in "0123456789abcdef"
        for character in text
    )


def _quote_capture_issues(
    trade,
    prefix,
):
    """
    Validate one entry/exit quote observation.

    AVAILABLE means both sides of the market and calculated
    spread data should exist.

    PARTIAL, UNAVAILABLE and ERROR are legitimate research
    outcomes as long as Northstar explicitly recorded them.
    """

    issues = []

    status_field = (
        f"{prefix}_quote_status"
    )

    source_field = (
        f"{prefix}_quote_source"
    )

    timestamp_field = (
        f"{prefix}_quote_timestamp"
    )

    error_field = (
        f"{prefix}_quote_error"
    )

    status = str(
        trade.get(
            status_field,
            "",
        )
        or ""
    ).strip().upper()

    allowed_statuses = {
        "AVAILABLE",
        "PARTIAL",
        "UNAVAILABLE",
        "ERROR",
    }

    if status not in allowed_statuses:
        issues.append(
            status_field
        )

    if not _capture_text(
        trade.get(
            source_field,
            "",
        )
    ):
        issues.append(
            source_field
        )

    if not _capture_text(
        trade.get(
            timestamp_field,
            "",
        )
    ):
        issues.append(
            timestamp_field
        )

    bid_field = f"{prefix}_bid"
    ask_field = f"{prefix}_ask"
    last_field = f"{prefix}_last"

    midpoint_field = (
        f"{prefix}_midpoint"
    )

    spread_amount_field = (
        f"{prefix}_spread_amount"
    )

    spread_percent_field = (
        f"{prefix}_spread_percent"
    )

    if status == "AVAILABLE":
        for field in (
            bid_field,
            ask_field,
            midpoint_field,
            spread_amount_field,
            spread_percent_field,
        ):
            minimum = (
                0
                if field in (
                    spread_amount_field,
                    spread_percent_field,
                )
                else None
            )

            if not _capture_number(
                trade.get(
                    field,
                    "",
                ),
                minimum=minimum,
            ):
                issues.append(
                    field
                )

    elif status == "PARTIAL":
        bid_ok = _capture_number(
            trade.get(
                bid_field,
                "",
            )
        )

        ask_ok = _capture_number(
            trade.get(
                ask_field,
                "",
            )
        )

        if not (
            bid_ok
            or ask_ok
        ):
            issues.extend(
                [
                    bid_field,
                    ask_field,
                ]
            )

    elif status in {
        "UNAVAILABLE",
        "ERROR",
    }:
        if not _capture_text(
            trade.get(
                error_field,
                "",
            )
        ):
            issues.append(
                error_field
            )

    # Last price is useful when supplied, but it is not
    # mandatory for an explicitly UNAVAILABLE observation.
    if (
        status
        in {
            "AVAILABLE",
            "PARTIAL",
        }
        and not _capture_number(
            trade.get(
                last_field,
                "",
            )
        )
    ):
        issues.append(
            last_field
        )

    return list(
        dict.fromkeys(
            issues
        )
    )


def missing_200_trade_capture_fields(
    trade,
):
    """
    Return missing/invalid fields grouped by research area.

    This validates whether Northstar captured the observation,
    not whether IBKR happened to provide every desired value.
    """

    issues = {
        group: []
        for group in CAPTURE_GROUP_NAMES
    }

    # --------------------------------------------------------
    # Full signal snapshot.
    # --------------------------------------------------------
    for field in (
        "signal_date",
        "signal_reason",
    ):
        if not _capture_text(
            trade.get(
                field,
                "",
            )
        ):
            issues[
                "signal_snapshot"
            ].append(
                field
            )

    if not _capture_number(
        trade.get(
            "signal_close",
            "",
        ),
        strictly_positive=True,
    ):
        issues[
            "signal_snapshot"
        ].append(
            "signal_close"
        )

    if not _capture_json_object(
        trade.get(
            "signal_snapshot_json",
            "",
        )
    ):
        issues[
            "signal_snapshot"
        ].append(
            "signal_snapshot_json"
        )

    # --------------------------------------------------------
    # Entry-time portfolio and risk context.
    # --------------------------------------------------------
    if (
        str(
            trade.get(
                "entry_context_status",
                "",
            )
            or ""
        ).strip().upper()
        != "AVAILABLE"
    ):
        issues[
            "entry_context"
        ].append(
            "entry_context_status"
        )

    numeric_context_fields = [
        (
            "entry_cash_before",
            0,
            False,
        ),
        (
            "entry_portfolio_value_before",
            None,
            True,
        ),
        (
            "entry_open_position_value_before",
            0,
            False,
        ),
        (
            "entry_portfolio_exposure_before",
            0,
            False,
        ),
        (
            "entry_open_positions_before",
            0,
            False,
        ),
        (
            "entry_closed_trades_before",
            0,
            False,
        ),
        (
            "entry_position_value",
            None,
            True,
        ),
        (
            "entry_initial_risk_per_share",
            None,
            True,
        ),
        (
            "entry_initial_risk_amount",
            None,
            True,
        ),
        (
            "entry_risk_budget",
            None,
            True,
        ),
        (
            "entry_max_position_value",
            None,
            True,
        ),
        (
            "entry_atr_multiplier",
            None,
            True,
        ),
        (
            "entry_reward_multiplier",
            None,
            True,
        ),
        (
            "entry_max_hold_days",
            None,
            True,
        ),
        (
            "signal_to_entry_gap_percent",
            None,
            False,
        ),
    ]

    for (
        field,
        minimum,
        strictly_positive,
    ) in numeric_context_fields:
        if not _capture_number(
            trade.get(
                field,
                "",
            ),
            minimum=minimum,
            strictly_positive=(
                strictly_positive
            ),
        ):
            issues[
                "entry_context"
            ].append(
                field
            )

    for field in (
        "entry_risk_model",
        "entry_sizing_limiting_factor",
        "entry_sizing_decision",
    ):
        if not _capture_text(
            trade.get(
                field,
                "",
            )
        ):
            issues[
                "entry_context"
            ].append(
                field
            )

    sizing_decision = str(
        trade.get(
            "entry_sizing_decision",
            "",
        )
        or ""
    ).strip().upper()

    if (
        sizing_decision
        not in {
            "ACCEPTED",
            "OVERRIDE",
        }
    ):
        if (
            "entry_sizing_decision"
            not in issues[
                "entry_context"
            ]
        ):
            issues[
                "entry_context"
            ].append(
                "entry_sizing_decision"
            )

    # --------------------------------------------------------
    # Runtime/config/code identity.
    # --------------------------------------------------------
    if not _capture_hex_digest(
        trade.get(
            "entry_git_commit",
            "",
        ),
        40,
    ):
        issues[
            "entry_fingerprint"
        ].append(
            "entry_git_commit"
        )

    if not _capture_text(
        trade.get(
            "entry_project_version",
            "",
        )
    ):
        issues[
            "entry_fingerprint"
        ].append(
            "entry_project_version"
        )

    for field in (
        "entry_config_sha256",
        "entry_strategy_code_sha256",
    ):
        if not _capture_hex_digest(
            trade.get(
                field,
                "",
            ),
            64,
        ):
            issues[
                "entry_fingerprint"
            ].append(
                field
            )

    if not _capture_json_object(
        trade.get(
            "entry_config_snapshot_json",
            "",
        )
    ):
        issues[
            "entry_fingerprint"
        ].append(
            "entry_config_snapshot_json"
        )

    if (
        str(
            trade.get(
                "entry_fingerprint_status",
                "",
            )
            or ""
        ).strip().upper()
        != "AVAILABLE"
    ):
        issues[
            "entry_fingerprint"
        ].append(
            "entry_fingerprint_status"
        )

    # --------------------------------------------------------
    # Entry/exit market microstructure observations.
    # --------------------------------------------------------
    issues[
        "entry_quote"
    ].extend(
        _quote_capture_issues(
            trade,
            "entry",
        )
    )

    issues[
        "exit_quote"
    ].extend(
        _quote_capture_issues(
            trade,
            "exit",
        )
    )

    # --------------------------------------------------------
    # One-minute completed-trade path.
    # --------------------------------------------------------
    path_status = str(
        trade.get(
            "trade_path_status",
            "",
        )
        or ""
    ).strip().upper()

    if (
        path_status
        not in {
            "COMPLETE",
            "NO_DATA",
            "ERROR",
        }
    ):
        issues[
            "trade_path"
        ].append(
            "trade_path_status"
        )

    if not _capture_text(
        trade.get(
            "trade_path_source",
            "",
        )
    ):
        issues[
            "trade_path"
        ].append(
            "trade_path_source"
        )

    for field in (
        "trade_path_bar_count",
        "trade_path_bars_saved",
    ):
        if not _capture_number(
            trade.get(
                field,
                "",
            ),
            minimum=0,
        ):
            issues[
                "trade_path"
            ].append(
                field
            )

    if path_status == "COMPLETE":
        if not _capture_number(
            trade.get(
                "trade_path_bar_count",
                "",
            ),
            strictly_positive=True,
        ):
            if (
                "trade_path_bar_count"
                not in issues[
                    "trade_path"
                ]
            ):
                issues[
                    "trade_path"
                ].append(
                    "trade_path_bar_count"
                )

        for field in (
            "highest_price",
            "lowest_price",
            "mfe_amount",
            "mfe_percent",
            "mfe_r",
            "mae_amount",
            "mae_percent",
            "mae_r",
        ):
            if not _capture_number(
                trade.get(
                    field,
                    "",
                ),
                minimum=0,
            ):
                issues[
                    "trade_path"
                ].append(
                    field
                )

        for field in (
            "mfe_timestamp",
            "mae_timestamp",
        ):
            if not _capture_text(
                trade.get(
                    field,
                    "",
                )
            ):
                issues[
                    "trade_path"
                ].append(
                    field
                )

    elif path_status == "ERROR":
        if not _capture_text(
            trade.get(
                "trade_path_error",
                "",
            )
        ):
            issues[
                "trade_path"
            ].append(
                "trade_path_error"
            )

    return {
        group: list(
            dict.fromkeys(
                group_issues
            )
        )
        for (
            group,
            group_issues,
        ) in issues.items()
        if group_issues
    }


def analyze_200_trade_capture_integrity(
    trades,
    monitor_start_date=(
        CAPTURE_MONITOR_START_DATE
    ),
):
    """
    Audit the new validation-sample research capture.

    PASS means every monitored completed trade contains a
    valid recorded outcome for every capture group.

    Data availability is reported separately because an
    explicit IBKR/Yahoo unavailable/error observation is still
    useful evidence that the capture pipeline ran.
    """

    total_trade_count = len(
        trades
    )

    monitored_trade_count = 0
    legacy_trade_count = 0
    undated_trade_count = 0

    complete_capture_count = 0
    incomplete_capture_count = 0

    group_issue_counts = {
        group: 0
        for group in CAPTURE_GROUP_NAMES
    }

    field_issue_counts = {}

    incomplete_trades = []

    entry_quote_status_counts = {}
    exit_quote_status_counts = {}
    trade_path_status_counts = {}

    fully_available_count = 0

    for trade in trades:
        entry_date = _parse_entry_date(
            trade.get(
                "entry_date",
                "",
            )
        )

        if entry_date is None:
            undated_trade_count += 1
            continue

        if entry_date < monitor_start_date:
            legacy_trade_count += 1
            continue

        monitored_trade_count += 1

        entry_quote_status = str(
            trade.get(
                "entry_quote_status",
                "",
            )
            or ""
        ).strip().upper()

        exit_quote_status = str(
            trade.get(
                "exit_quote_status",
                "",
            )
            or ""
        ).strip().upper()

        path_status = str(
            trade.get(
                "trade_path_status",
                "",
            )
            or ""
        ).strip().upper()

        entry_quote_status_counts[
            entry_quote_status or "MISSING"
        ] = (
            entry_quote_status_counts.get(
                entry_quote_status
                or "MISSING",
                0,
            )
            + 1
        )

        exit_quote_status_counts[
            exit_quote_status or "MISSING"
        ] = (
            exit_quote_status_counts.get(
                exit_quote_status
                or "MISSING",
                0,
            )
            + 1
        )

        trade_path_status_counts[
            path_status or "MISSING"
        ] = (
            trade_path_status_counts.get(
                path_status
                or "MISSING",
                0,
            )
            + 1
        )

        if (
            entry_quote_status
            == "AVAILABLE"
            and exit_quote_status
            == "AVAILABLE"
            and path_status
            == "COMPLETE"
        ):
            fully_available_count += 1

        issues = (
            missing_200_trade_capture_fields(
                trade
            )
        )

        if not issues:
            complete_capture_count += 1
            continue

        incomplete_capture_count += 1

        flattened_fields = []

        for (
            group,
            fields,
        ) in issues.items():
            group_issue_counts[
                group
            ] += 1

            for field in fields:
                field_issue_counts[
                    field
                ] = (
                    field_issue_counts.get(
                        field,
                        0,
                    )
                    + 1
                )

                flattened_fields.append(
                    field
                )

        incomplete_trades.append(
            {
                "symbol": str(
                    trade.get(
                        "symbol",
                        "--",
                    )
                ),
                "strategy": str(
                    trade.get(
                        "strategy",
                        "--",
                    )
                ),
                "entry_date": (
                    entry_date.isoformat()
                ),
                "groups": list(
                    issues.keys()
                ),
                "fields": list(
                    dict.fromkeys(
                        flattened_fields
                    )
                ),
            }
        )

    if monitored_trade_count == 0:
        integrity_status = (
            "NO_MONITORED_TRADES_YET"
        )

    elif incomplete_capture_count:
        integrity_status = "FAIL"

    else:
        integrity_status = "PASS"

    capture_coverage_percent = (
        (
            complete_capture_count
            / monitored_trade_count
        )
        * 100.0
        if monitored_trade_count
        else 0.0
    )

    if monitored_trade_count:
        if (
            fully_available_count
            == monitored_trade_count
        ):
            data_availability_status = (
                "COMPLETE"
            )
        else:
            data_availability_status = (
                "PARTIAL"
            )

    else:
        data_availability_status = (
            "NO_MONITORED_TRADES_YET"
        )

    return {
        "integrity_status": (
            integrity_status
        ),
        "monitor_start_date": (
            monitor_start_date.isoformat()
        ),
        "total_trade_count": (
            total_trade_count
        ),
        "legacy_trade_count": (
            legacy_trade_count
        ),
        "undated_trade_count": (
            undated_trade_count
        ),
        "monitored_trade_count": (
            monitored_trade_count
        ),
        "complete_capture_count": (
            complete_capture_count
        ),
        "incomplete_capture_count": (
            incomplete_capture_count
        ),
        "capture_coverage_percent": (
            capture_coverage_percent
        ),
        "group_issue_counts": (
            group_issue_counts
        ),
        "field_issue_counts": (
            field_issue_counts
        ),
        "incomplete_trades": (
            incomplete_trades
        ),
        "entry_quote_status_counts": (
            entry_quote_status_counts
        ),
        "exit_quote_status_counts": (
            exit_quote_status_counts
        ),
        "trade_path_status_counts": (
            trade_path_status_counts
        ),
        "data_availability_status": (
            data_availability_status
        ),
        "fully_available_count": (
            fully_available_count
        ),
    }


def analyze_200_trade_capture_integrity_journal(
    file_path,
    monitor_start_date=(
        CAPTURE_MONITOR_START_DATE
    ),
):
    """
    Audit one completed paper-trade journal read-only.
    """

    trades = load_completed_trades(
        file_path
    )

    return (
        analyze_200_trade_capture_integrity(
            trades,
            monitor_start_date=(
                monitor_start_date
            ),
        )
    )

