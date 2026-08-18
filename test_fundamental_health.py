import pandas as pd

from research.fundamental_health import (
    calculate_fundamental_health,
    classify_leverage,
    classify_payout,
)


def frame(rows):
    return pd.DataFrame(
        rows,
        index=[
            "2025-12-31",
            "2024-12-31",
        ],
    ).T


def sample_bundle():
    return {
        "info": {
            "marketCap": 80_000_000_000,
            "freeCashflow": 5_600_000_000,
            "operatingCashflow": 12_000_000_000,
            "totalRevenue": 54_000_000_000,
            "ebitda": 14_000_000_000,
            "netIncomeToCommon": 6_500_000_000,
            "revenueGrowth": 0.20,
            "earningsGrowth": 0.25,
            "dividendYield": 2.0,
            "payoutRatio": 0.25,
            "totalCash": 3_000_000_000,
            "totalDebt": 11_000_000_000,
            "debtToEquity": 35.0,
            "returnOnEquity": 0.20,
            "returnOnAssets": 0.09,
            "profitMargins": 0.12,
            "operatingMargins": 0.23,
        },
        "income_stmt": frame(
            {
                "Total Revenue": [
                    52_000_000_000,
                    55_000_000_000,
                ],
                "EBITDA": [
                    10_500_000_000,
                    9_500_000_000,
                ],
                "Net Income": [
                    4_000_000_000,
                    3_000_000_000,
                ],
            }
        ),
        "cash_flow": frame(
            {
                "Operating Cash Flow": [
                    8_000_000_000,
                    9_000_000_000,
                ],
                "Free Cash Flow": [
                    3_300_000_000,
                    4_200_000_000,
                ],
            }
        ),
        "balance_sheet": frame(
            {
                "Total Debt": [
                    14_000_000_000,
                    10_500_000_000,
                ],
            }
        ),
    }


def test_current_metrics():
    def provider(symbol):
        return sample_bundle()

    result = (
        calculate_fundamental_health(
            "TEST.TO",
            fundamental_provider=provider,
        )
    )

    current = result["current"]

    assert result["status"] == "AVAILABLE"
    assert current["fcf_yield_percent"] == 7.0
    assert current["dividend_yield_percent"] == 2.0
    assert current["payout_ratio_percent"] == 25.0
    assert current["net_debt"] == 8_000_000_000
    assert current["net_debt_to_ebitda"] == 0.57

    assert (
        current["leverage_context"]
        == "LOW_NET_DEBT"
    )

    assert (
        current["profit_margin_percent"]
        == 12.0
    )

    assert result["research_only"] is True


def test_mixed_trends_are_preserved():
    def provider(symbol):
        return sample_bundle()

    result = (
        calculate_fundamental_health(
            "TEST.TO",
            fundamental_provider=provider,
        )
    )

    trends = result[
        "annual_trends"
    ]

    assert (
        trends["revenue"]["direction"]
        == "DECLINING"
    )

    assert (
        trends["ebitda"]["direction"]
        == "IMPROVING"
    )

    assert (
        trends["net_income"]["direction"]
        == "IMPROVING"
    )

    assert (
        trends[
            "free_cash_flow"
        ]["direction"]
        == "DECLINING"
    )

    assert (
        trends["debt"]["direction"]
        == "INCREASING"
    )

    assert (
        result["trend_context"]
        == "MIXED_TRENDS"
    )

    assert (
        result["fundamental_context"]
        == "HEALTHY_WITH_MIXED_TRENDS"
    )


def test_classifiers():
    assert (
        classify_leverage(-0.2)
        == "NET_CASH"
    )

    assert (
        classify_leverage(0.8)
        == "LOW_NET_DEBT"
    )

    assert (
        classify_leverage(2.5)
        == "ELEVATED_NET_DEBT"
    )

    assert (
        classify_leverage(4.0)
        == "HIGH_NET_DEBT"
    )

    assert (
        classify_payout(25)
        == "LOW_PAYOUT"
    )

    assert (
        classify_payout(80)
        == "HIGH_PAYOUT"
    )

    assert (
        classify_payout(120)
        == "ABOVE_EARNINGS"
    )


def test_fractional_dividend_yield():
    bundle = sample_bundle()

    bundle["info"][
        "dividendYield"
    ] = 0.025

    def provider(symbol):
        return bundle

    result = (
        calculate_fundamental_health(
            "TEST.TO",
            fundamental_provider=provider,
        )
    )

    assert (
        result["current"][
            "dividend_yield_percent"
        ]
        == 2.5
    )


def test_provider_failure_is_fail_soft():
    def provider(symbol):
        raise RuntimeError(
            "Yahoo unavailable"
        )

    result = (
        calculate_fundamental_health(
            "ABC.TO",
            fundamental_provider=provider,
        )
    )

    assert result["status"] == "UNAVAILABLE"

    assert (
        "Yahoo unavailable"
        in result["reason"]
    )

    assert result["research_only"] is True
