import pytest

from research.stock_research_dashboard import (
    build_stock_research_report,
    normalize_tsx_symbol,
)


def test_normalize_tsx_symbol():
    assert (
        normalize_tsx_symbol(
            "DOL"
        )
        == "DOL.TO"
    )

    assert (
        normalize_tsx_symbol(
            " dol.to "
        )
        == "DOL.TO"
    )

    assert (
        normalize_tsx_symbol(
            "TECK-B"
        )
        == "TECK-B.TO"
    )


def test_blank_symbol_is_rejected():
    with pytest.raises(
        ValueError
    ):
        normalize_tsx_symbol(
            "   "
        )


def test_arbitrary_symbol_runs_all_research_components():
    calls = []

    def quote(symbol):
        calls.append(
            (
                "quote",
                symbol,
            )
        )

        return {
            "status": "AVAILABLE",
            "price": 150.0,
            "bid": 149.9,
            "ask": 150.1,
            "source": "IBKR",
        }

    def market(date):
        calls.append(
            (
                "market",
                date,
            )
        )

        return {
            "status": "AVAILABLE",
            "regime": "BULL",
            "data_source": (
                "IBKR_TRADES"
            ),
        }

    def relative(
        symbol,
        date,
    ):
        calls.append(
            (
                "relative",
                symbol,
                date,
            )
        )

        return {
            "status": "AVAILABLE",
            "rs_xic_20": 4.2,
            "rs_xiu_20": 3.8,
            "data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
        }

    def moving(
        symbol,
        date,
    ):
        calls.append(
            (
                "moving",
                symbol,
                date,
            )
        )

        return {
            "status": "AVAILABLE",
            "trend_alignment": (
                "STRONG_UPTREND"
            ),
            "sma_20": 145.0,
            "sma_50": 140.0,
            "sma_200": 125.0,
            "data_source": (
                "IBKR_TRADES"
            ),
        }

    def volatility(
        symbol,
        date,
    ):
        calls.append(
            (
                "volatility",
                symbol,
                date,
            )
        )

        return {
            "status": "AVAILABLE",
            "atr_14": 3.2,
            "atr_percent": 2.13,
            "volatility_regime": (
                "NORMAL"
            ),
            "data_source": (
                "IBKR_TRADES"
            ),
        }

    def oversold(
        symbol,
        date,
    ):
        calls.append(
            (
                "oversold",
                symbol,
                date,
            )
        )

        return {
            "status": "AVAILABLE",
            "overall_context": "PULLBACK",
            "recovery_state": (
                "PULLBACK_NOT_OVERSOLD"
            ),
            "rsi_14": 45.6,
            "research_only": True,
        }

    report = (
        build_stock_research_report(
            "DOL",
            measurement_date=(
                "2026-08-17"
            ),
            quote_provider=quote,
            market_regime_provider=(
                market
            ),
            relative_strength_provider=(
                relative
            ),
            moving_average_provider=(
                moving
            ),
            volatility_provider=(
                volatility
            ),
            oversold_provider=(
                oversold
            ),
        )
    )

    assert (
        report["symbol"]
        == "DOL.TO"
    )

    assert (
        report["read_only"]
        is True
    )

    assert (
        report["mode"]
        == "READ_ONLY_STOCK_RESEARCH"
    )

    assert (
        report["status"]
        == "COMPLETE"
    )

    assert (
        report[
            "available_components"
        ]
        == 6
    )

    assert (
        report["quote"]["price"]
        == 150.0
    )

    assert (
        report[
            "market_regime"
        ]["regime"]
        == "BULL"
    )

    assert (
        report[
            "relative_strength"
        ]["rs_xic_20"]
        == 4.2
    )

    assert (
        report[
            "moving_average"
        ]["trend_alignment"]
        == "STRONG_UPTREND"
    )

    assert (
        report[
            "volatility"
        ]["volatility_regime"]
        == "NORMAL"
    )

    assert (
        report[
            "oversold"
        ]["overall_context"]
        == "PULLBACK"
    )

    assert (
        report[
            "oversold"
        ]["research_only"]
        is True
    )

    assert (
        (
            "quote",
            "DOL.TO",
        )
        in calls
    )

    assert (
        (
            "relative",
            "DOL.TO",
            "2026-08-17",
        )
        in calls
    )

    assert (
        (
            "oversold",
            "DOL.TO",
            "2026-08-17",
        )
        in calls
    )


def test_one_failed_component_does_not_break_report():
    def broken_quote(
        symbol,
    ):
        raise ConnectionError(
            "TWS unavailable"
        )

    def market(date):
        return {
            "status": "AVAILABLE",
            "regime": "BULL",
        }

    def research(
        symbol,
        date,
    ):
        return {
            "status": "AVAILABLE",
        }

    report = (
        build_stock_research_report(
            "WCP.TO",
            measurement_date=(
                "2026-08-17"
            ),
            quote_provider=(
                broken_quote
            ),
            market_regime_provider=(
                market
            ),
            relative_strength_provider=(
                research
            ),
            moving_average_provider=(
                research
            ),
            volatility_provider=(
                research
            ),
            oversold_provider=(
                research
            ),
        )
    )

    assert (
        report["status"]
        == "PARTIAL"
    )

    assert (
        report["quote"]["status"]
        == "UNAVAILABLE"
    )

    assert (
        "TWS unavailable"
        in report[
            "quote"
        ]["reason"]
    )

    assert (
        report[
            "available_components"
        ]
        == 5
    )


def test_research_report_has_no_trading_actions():
    def available(*args):
        return {
            "status": "AVAILABLE",
        }

    report = (
        build_stock_research_report(
            "BCE",
            measurement_date=(
                "2026-08-17"
            ),
            quote_provider=available,
            market_regime_provider=(
                available
            ),
            relative_strength_provider=(
                available
            ),
            moving_average_provider=(
                available
            ),
            volatility_provider=(
                available
            ),
            oversold_provider=(
                available
            ),
        )
    )

    forbidden = {
        "queue_trade",
        "place_order",
        "pending_trade",
        "position",
        "execute",
    }

    assert (
        forbidden
        .intersection(
            report.keys()
        )
        == set()
    )
