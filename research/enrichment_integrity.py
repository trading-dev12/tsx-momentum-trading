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
