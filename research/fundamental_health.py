"""
Northstar Quant
Fundamental Health Research

Read-only business-quality and financial-direction context
for arbitrary TSX stocks.

No BUY signal is produced and no strategy, scanner, queue,
portfolio, or validation sample is modified.
"""

from __future__ import annotations

import math

import pandas as pd
import yfinance as yf


def _number(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(result):
        return None

    return result


def _ratio_percent(value):
    value = _number(value)

    if value is None:
        return None

    return value * 100.0


def _dividend_percent(value):
    """
    yfinance versions can expose dividendYield either as
    a fraction or as percentage points.
    """

    value = _number(value)

    if value is None:
        return None

    if abs(value) <= 0.20:
        return value * 100.0

    return value


def _percent_change(
    current,
    previous,
):
    current = _number(current)
    previous = _number(previous)

    if (
        current is None
        or previous is None
        or previous == 0
    ):
        return None

    return (
        (current - previous)
        / abs(previous)
        * 100.0
    )


def classify_operating_trend(
    change_percent,
):
    if change_percent is None:
        return "UNAVAILABLE"

    if change_percent >= 5:
        return "IMPROVING"

    if change_percent <= -5:
        return "DECLINING"

    return "STABLE"


def classify_debt_trend(
    change_percent,
):
    if change_percent is None:
        return "UNAVAILABLE"

    if change_percent >= 5:
        return "INCREASING"

    if change_percent <= -5:
        return "DECREASING"

    return "STABLE"


def classify_leverage(
    net_debt_to_ebitda,
):
    if net_debt_to_ebitda is None:
        return "UNAVAILABLE"

    if net_debt_to_ebitda < 0:
        return "NET_CASH"

    if net_debt_to_ebitda < 1:
        return "LOW_NET_DEBT"

    if net_debt_to_ebitda < 2:
        return "MODERATE_NET_DEBT"

    if net_debt_to_ebitda < 3:
        return "ELEVATED_NET_DEBT"

    return "HIGH_NET_DEBT"


def classify_payout(
    payout_percent,
):
    if (
        payout_percent is None
        or payout_percent < 0
    ):
        return "UNAVAILABLE"

    if payout_percent <= 50:
        return "LOW_PAYOUT"

    if payout_percent <= 75:
        return "MODERATE_PAYOUT"

    if payout_percent <= 100:
        return "HIGH_PAYOUT"

    return "ABOVE_EARNINGS"


def _latest_two(
    table,
    row_name,
):
    if (
        table is None
        or not isinstance(
            table,
            pd.DataFrame,
        )
        or table.empty
        or row_name not in table.index
    ):
        return (
            None,
            None,
            None,
            None,
        )

    values = []

    for column in table.columns:
        value = _number(
            table.loc[
                row_name,
                column,
            ]
        )

        if value is None:
            continue

        timestamp = pd.to_datetime(
            column,
            errors="coerce",
        )

        values.append(
            (
                timestamp,
                str(column),
                value,
            )
        )

    if len(values) < 2:
        return (
            None,
            None,
            None,
            None,
        )

    dated = [
        item
        for item in values
        if not pd.isna(
            item[0]
        )
    ]

    if len(dated) >= 2:
        dated.sort(
            key=lambda item: item[0],
            reverse=True,
        )
        values = dated

    latest = values[0]
    previous = values[1]

    return (
        latest[2],
        previous[2],
        latest[1],
        previous[1],
    )


def _operating_trend(
    table,
    row_name,
):
    (
        latest,
        previous,
        latest_period,
        previous_period,
    ) = _latest_two(
        table,
        row_name,
    )

    change = _percent_change(
        latest,
        previous,
    )

    return {
        "latest": latest,
        "previous": previous,
        "latest_period": (
            latest_period
        ),
        "previous_period": (
            previous_period
        ),
        "change_percent": (
            round(change, 2)
            if change is not None
            else None
        ),
        "direction": (
            classify_operating_trend(
                change
            )
        ),
    }


def _debt_trend(
    table,
):
    (
        latest,
        previous,
        latest_period,
        previous_period,
    ) = _latest_two(
        table,
        "Total Debt",
    )

    change = _percent_change(
        latest,
        previous,
    )

    return {
        "latest": latest,
        "previous": previous,
        "latest_period": (
            latest_period
        ),
        "previous_period": (
            previous_period
        ),
        "change_percent": (
            round(change, 2)
            if change is not None
            else None
        ),
        "direction": (
            classify_debt_trend(
                change
            )
        ),
    }


def load_fundamental_bundle(
    symbol,
):
    ticker = yf.Ticker(
        symbol
    )

    return {
        "info": dict(
            ticker.info or {}
        ),
        "income_stmt": (
            ticker.income_stmt
        ),
        "cash_flow": (
            ticker.cash_flow
        ),
        "balance_sheet": (
            ticker.balance_sheet
        ),
    }


def _trend_context(
    annual_trends,
    revenue_growth,
    earnings_growth,
):
    improving = 0
    weakening = 0
    stable = 0

    for name, result in (
        annual_trends.items()
    ):
        direction = result.get(
            "direction"
        )

        if name == "debt":
            if (
                direction
                == "DECREASING"
            ):
                improving += 1

            elif (
                direction
                == "INCREASING"
            ):
                weakening += 1

            elif direction == "STABLE":
                stable += 1

            continue

        if direction == "IMPROVING":
            improving += 1

        elif direction == "DECLINING":
            weakening += 1

        elif direction == "STABLE":
            stable += 1

    for growth in (
        revenue_growth,
        earnings_growth,
    ):
        if growth is None:
            continue

        if growth >= 5:
            improving += 1

        elif growth <= -5:
            weakening += 1

        else:
            stable += 1

    if (
        improving >= 3
        and weakening <= 1
    ):
        context = "IMPROVING"

    elif (
        weakening >= 3
        and improving <= 1
    ):
        context = "DETERIORATING"

    elif (
        improving >= 2
        and weakening >= 2
    ):
        context = "MIXED_TRENDS"

    elif weakening > improving:
        context = "LEANING_WEAKER"

    elif improving > weakening:
        context = "LEANING_STRONGER"

    else:
        context = "STABLE_OR_MIXED"

    return {
        "context": context,
        "improving": improving,
        "weakening": weakening,
        "stable": stable,
    }


def _financial_base(
    free_cash_flow,
    operating_cash_flow,
    net_income,
    net_debt_to_ebitda,
):
    positive_count = sum(
        value is not None
        and value > 0
        for value in (
            free_cash_flow,
            operating_cash_flow,
            net_income,
        )
    )

    leverage_ok = (
        net_debt_to_ebitda
        is None
        or net_debt_to_ebitda < 3
    )

    if (
        positive_count == 3
        and leverage_ok
    ):
        return "FINANCIALLY_SOUND"

    if (
        positive_count >= 2
        and leverage_ok
    ):
        return "GENERALLY_SOUND"

    if positive_count >= 2:
        return "MIXED_WITH_LEVERAGE"

    return "WEAK_OR_INCOMPLETE"


def _overall_context(
    financial_base,
    trend_context,
):
    if (
        financial_base
        == "FINANCIALLY_SOUND"
    ):
        if (
            trend_context
            == "IMPROVING"
        ):
            return (
                "HEALTHY_AND_IMPROVING"
            )

        if trend_context in {
            "MIXED_TRENDS",
            "STABLE_OR_MIXED",
            "LEANING_STRONGER",
        }:
            return (
                "HEALTHY_WITH_MIXED_TRENDS"
            )

        return (
            "SOUND_BUT_WEAKENING"
        )

    if financial_base in {
        "GENERALLY_SOUND",
        "MIXED_WITH_LEVERAGE",
    }:
        if (
            trend_context
            == "IMPROVING"
        ):
            return (
                "MIXED_BUT_IMPROVING"
            )

        if (
            trend_context
            == "DETERIORATING"
        ):
            return (
                "MIXED_AND_WEAKENING"
            )

        return "MIXED"

    return "WEAK_OR_INCOMPLETE"


def calculate_fundamental_health(
    symbol,
    fundamental_provider=(
        load_fundamental_bundle
    ),
):
    normalized_symbol = str(
        symbol or ""
    ).strip().upper()

    if not normalized_symbol:
        return {
            "status": "UNAVAILABLE",
            "reason": (
                "Symbol is required."
            ),
        }

    try:
        bundle = (
            fundamental_provider(
                normalized_symbol
            )
        )

        info = dict(
            bundle.get(
                "info"
            )
            or {}
        )

        income = bundle.get(
            "income_stmt"
        )

        cash_flow = bundle.get(
            "cash_flow"
        )

        balance = bundle.get(
            "balance_sheet"
        )

        market_cap = _number(
            info.get(
                "marketCap"
            )
        )

        free_cash_flow = _number(
            info.get(
                "freeCashflow"
            )
        )

        operating_cash_flow = (
            _number(
                info.get(
                    "operatingCashflow"
                )
            )
        )

        revenue = _number(
            info.get(
                "totalRevenue"
            )
        )

        ebitda = _number(
            info.get(
                "ebitda"
            )
        )

        net_income = _number(
            info.get(
                "netIncomeToCommon"
            )
        )

        total_cash = _number(
            info.get(
                "totalCash"
            )
        )

        total_debt = _number(
            info.get(
                "totalDebt"
            )
        )

        fcf_yield = None

        if (
            market_cap
            and free_cash_flow
            is not None
        ):
            fcf_yield = (
                free_cash_flow
                / market_cap
                * 100.0
            )

        net_debt = None

        if (
            total_debt is not None
            and total_cash is not None
        ):
            net_debt = (
                total_debt
                - total_cash
            )

        net_debt_to_ebitda = None

        if (
            net_debt is not None
            and ebitda
            and ebitda > 0
        ):
            net_debt_to_ebitda = (
                net_debt
                / ebitda
            )

        revenue_growth = (
            _ratio_percent(
                info.get(
                    "revenueGrowth"
                )
            )
        )

        earnings_growth = (
            _ratio_percent(
                info.get(
                    "earningsGrowth"
                )
            )
        )

        annual_trends = {
            "revenue": (
                _operating_trend(
                    income,
                    "Total Revenue",
                )
            ),
            "ebitda": (
                _operating_trend(
                    income,
                    "EBITDA",
                )
            ),
            "net_income": (
                _operating_trend(
                    income,
                    "Net Income",
                )
            ),
            "operating_cash_flow": (
                _operating_trend(
                    cash_flow,
                    "Operating Cash Flow",
                )
            ),
            "free_cash_flow": (
                _operating_trend(
                    cash_flow,
                    "Free Cash Flow",
                )
            ),
            "debt": (
                _debt_trend(
                    balance
                )
            ),
        }

        trends = _trend_context(
            annual_trends,
            revenue_growth,
            earnings_growth,
        )

        financial_base = (
            _financial_base(
                free_cash_flow,
                operating_cash_flow,
                net_income,
                net_debt_to_ebitda,
            )
        )

        payout_percent = (
            _ratio_percent(
                info.get(
                    "payoutRatio"
                )
            )
        )

        return {
            "symbol": (
                normalized_symbol
            ),
            "status": "AVAILABLE",
            "reason": "",
            "data_source": (
                "YAHOO_INFO_AND_STATEMENTS"
            ),
            "fundamental_context": (
                _overall_context(
                    financial_base,
                    trends["context"],
                )
            ),
            "financial_base": (
                financial_base
            ),
            "trend_context": (
                trends["context"]
            ),
            "trend_counts": {
                "improving": (
                    trends["improving"]
                ),
                "weakening": (
                    trends["weakening"]
                ),
                "stable": (
                    trends["stable"]
                ),
            },
            "current": {
                "market_cap": market_cap,
                "free_cash_flow": (
                    free_cash_flow
                ),
                "fcf_yield_percent": (
                    round(
                        fcf_yield,
                        2,
                    )
                    if fcf_yield
                    is not None
                    else None
                ),
                "operating_cash_flow": (
                    operating_cash_flow
                ),
                "revenue": revenue,
                "ebitda": ebitda,
                "net_income": net_income,
                "dividend_yield_percent": (
                    _dividend_percent(
                        info.get(
                            "dividendYield"
                        )
                    )
                ),
                "payout_ratio_percent": (
                    round(
                        payout_percent,
                        2,
                    )
                    if payout_percent
                    is not None
                    else None
                ),
                "payout_context": (
                    classify_payout(
                        payout_percent
                    )
                ),
                "total_cash": total_cash,
                "total_debt": total_debt,
                "net_debt": net_debt,
                "net_debt_to_ebitda": (
                    round(
                        net_debt_to_ebitda,
                        2,
                    )
                    if net_debt_to_ebitda
                    is not None
                    else None
                ),
                "leverage_context": (
                    classify_leverage(
                        net_debt_to_ebitda
                    )
                ),
                "debt_to_equity_percent": (
                    _number(
                        info.get(
                            "debtToEquity"
                        )
                    )
                ),
                "revenue_growth_percent": (
                    round(
                        revenue_growth,
                        2,
                    )
                    if revenue_growth
                    is not None
                    else None
                ),
                "earnings_growth_percent": (
                    round(
                        earnings_growth,
                        2,
                    )
                    if earnings_growth
                    is not None
                    else None
                ),
                "return_on_equity_percent": (
                    _ratio_percent(
                        info.get(
                            "returnOnEquity"
                        )
                    )
                ),
                "return_on_assets_percent": (
                    _ratio_percent(
                        info.get(
                            "returnOnAssets"
                        )
                    )
                ),
                "profit_margin_percent": (
                    _ratio_percent(
                        info.get(
                            "profitMargins"
                        )
                    )
                ),
                "operating_margin_percent": (
                    _ratio_percent(
                        info.get(
                            "operatingMargins"
                        )
                    )
                ),
            },
            "annual_trends": (
                annual_trends
            ),
            "research_only": True,
            "interpretation_note": (
                "Fundamental health is "
                "descriptive research context, "
                "not a BUY signal. Sector and "
                "commodity cycles can make "
                "year-over-year comparisons "
                "volatile."
            ),
        }

    except Exception as error:
        return {
            "symbol": (
                normalized_symbol
            ),
            "status": "UNAVAILABLE",
            "reason": str(
                error
            ),
            "data_source": (
                "YAHOO_INFO_AND_STATEMENTS"
            ),
            "research_only": True,
        }
