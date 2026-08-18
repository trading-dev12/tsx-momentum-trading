from mobile_dashboard.stock_research_ui import (
    inject_stock_research_form,
    render_stock_research_page,
)


def sample_report():
    return {
        "symbol": "DOL.TO",
        "status": "COMPLETE",
        "measurement_date": "2026-08-17",
        "quote": {
            "status": "AVAILABLE",
            "price": 150.0,
            "bid": 149.9,
            "ask": 150.1,
            "volume": 123456,
            "source": "IBKR",
        },
        "market_regime": {
            "status": "AVAILABLE",
            "regime": "BULL",
            "close_vs_sma_200_percent": 5.2,
            "sma_50_vs_sma_200_percent": 2.1,
        },
        "relative_strength": {
            "status": "AVAILABLE",
            "stock_return_20": 8.0,
            "rs_xic_20": 4.2,
            "rs_xiu_20": 3.8,
        },
        "moving_average": {
            "status": "AVAILABLE",
            "trend_alignment": "STRONG_UPTREND",
            "sma_20": 145.0,
            "sma_50": 140.0,
            "sma_200": 125.0,
            "close_vs_sma20_percent": 3.45,
            "close_vs_sma200_percent": 20.0,
        },
        "volatility": {
            "status": "AVAILABLE",
            "atr_14": 3.2,
            "atr_percent": 2.13,
            "realized_volatility_20": 22.4,
            "volatility_percentile_252": 48.0,
            "volatility_regime": "NORMAL",
        },
        "oversold": {
            "status": "AVAILABLE",
            "data_source": "IBKR_TRADES",
            "overall_context": "PULLBACK",
            "recovery_state": (
                "PULLBACK_NOT_OVERSOLD"
            ),
            "rsi_14": 45.6,
            "rsi_state": "NEUTRAL",
            "stoch_rsi_14": 0.0,
            "stoch_rsi_state": "OVERSOLD",
            "mfi_14": 50.7,
            "mfi_state": "NEUTRAL",
            "bollinger_percent_b": 0.32,
            "bollinger_state": (
                "INSIDE_BANDS"
            ),
            "atr_distance_from_sma20": -0.64,
            "atr_pullback_state": "NORMAL",
            "drawdown_from_52week_high_percent": 10.7,
            "distance_from_52week_low_percent": 13.0,
            "week_52_position_percent": 49.0,
            "oversold_signal_count": 1,
            "extension_signal_count": 0,
            "research_only": True,
        },
        "valuation": {
            "status": "AVAILABLE",
            "data_source": (
                "YAHOO_VALUATION_MEASURES"
            ),
            "valuation_context": "MIXED",
            "history_snapshot_count": 5,
            "below_recent_count": 2,
            "near_recent_count": 1,
            "above_recent_count": 3,
            "metrics": {
                "trailing_pe": {
                    "current": 11.98,
                    "recent_median": 13.42,
                    "vs_recent_median_percent": -10.8,
                    "context": (
                        "BELOW_RECENT_MEDIAN"
                    ),
                },
                "forward_pe": {
                    "current": 10.15,
                    "recent_median": 14.60,
                    "vs_recent_median_percent": -30.5,
                    "context": (
                        "WELL_BELOW_RECENT_MEDIAN"
                    ),
                },
                "price_sales": {
                    "current": 1.37,
                    "recent_median": 0.77,
                    "vs_recent_median_percent": 78.7,
                    "context": (
                        "WELL_ABOVE_RECENT_MEDIAN"
                    ),
                },
                "price_book": {
                    "current": 2.32,
                    "recent_median": 1.55,
                    "vs_recent_median_percent": 50.2,
                    "context": (
                        "WELL_ABOVE_RECENT_MEDIAN"
                    ),
                },
                "ev_revenue": {
                    "current": 1.52,
                    "recent_median": 0.94,
                    "vs_recent_median_percent": 60.6,
                    "context": (
                        "WELL_ABOVE_RECENT_MEDIAN"
                    ),
                },
                "ev_ebitda": {
                    "current": 5.96,
                    "recent_median": 5.58,
                    "vs_recent_median_percent": 6.8,
                    "context": (
                        "NEAR_RECENT_MEDIAN"
                    ),
                },
            },
            "research_only": True,
        },
        "fundamental_health": {
            "status": "AVAILABLE",
            "data_source": (
                "YAHOO_INFO_AND_STATEMENTS"
            ),
            "fundamental_context": (
                "HEALTHY_WITH_MIXED_TRENDS"
            ),
            "financial_base": (
                "FINANCIALLY_SOUND"
            ),
            "trend_context": (
                "MIXED_TRENDS"
            ),
            "current": {
                "fcf_yield_percent": 6.66,
                "dividend_yield_percent": 2.04,
                "payout_ratio_percent": 22.78,
                "payout_context": "LOW_PAYOUT",
                "net_debt_to_ebitda": 0.59,
                "leverage_context": (
                    "LOW_NET_DEBT"
                ),
                "revenue_growth_percent": 41.5,
                "earnings_growth_percent": 239.1,
                "return_on_equity_percent": 20.9,
                "return_on_assets_percent": 9.2,
                "profit_margin_percent": 12.4,
                "operating_margin_percent": 23.8,
            },
            "annual_trends": {
                "revenue": {
                    "change_percent": -8.62,
                    "direction": "DECLINING",
                },
                "ebitda": {
                    "change_percent": 7.71,
                    "direction": "IMPROVING",
                },
                "net_income": {
                    "change_percent": 25.08,
                    "direction": "IMPROVING",
                },
                "operating_cash_flow": {
                    "change_percent": -10.9,
                    "direction": "DECLINING",
                },
                "free_cash_flow": {
                    "change_percent": -21.3,
                    "direction": "DECLINING",
                },
                "debt": {
                    "change_percent": 33.6,
                    "direction": "INCREASING",
                },
            },
            "research_only": True,
        },
    }


def test_dashboard_form_is_injected():
    html = (
        "<html><body>"
        "<main>Dashboard</main>"
        "</body></html>"
    )

    result = (
        inject_stock_research_form(
            html
        )
    )

    assert (
        'id="stock-research-search"'
        in result
    )

    assert (
        'action="/stock-research"'
        in result
    )

    assert (
        'name="symbol"'
        in result
    )


def test_dashboard_form_is_not_duplicated():
    html = (
        "<html><body>"
        "<main>Dashboard</main>"
        "</body></html>"
    )

    once = (
        inject_stock_research_form(
            html
        )
    )

    twice = (
        inject_stock_research_form(
            once
        )
    )

    assert (
        twice.count(
            'id="stock-research-search"'
        )
        == 1
    )


def test_stock_research_page_renders_report():
    html = (
        render_stock_research_page(
            sample_report(),
            query="DOL",
        )
    )

    assert "DOL.TO" in html
    assert "BULL" in html
    assert "STRONG UPTREND" in html
    assert "RS vs XIC" in html
    assert "NORMAL" in html
    assert "$150.00" in html
    assert (
        "Pullback / Oversold Context"
        in html
    )
    assert "PULLBACK" in html
    assert "PULLBACK NOT OVERSOLD" in html
    assert "RSI 14" in html
    assert "45.6" in html
    assert "Stoch RSI" in html
    assert "OVERSOLD" in html
    assert "52W Drawdown" in html
    assert "10.7%" in html
    assert "Oversold Flags" in html
    assert "1 / 5" in html
    assert "Extension Flags" in html
    assert "0 / 5" in html
    assert "not a BUY signal" in html

    assert "Fundamental Valuation" in html
    assert "MIXED" in html
    assert "Trailing P/E" in html
    assert "11.98x" in html
    assert "Med 13.42x" in html
    assert "Fundamental Health / Value-Trap Check" in html
    assert "HEALTHY WITH MIXED TRENDS" in html
    assert "FINANCIALLY SOUND" in html
    assert "6.66%" in html
    assert "0.59x" in html
    assert "Annual Revenue Trend" in html
    assert "DECLINING" in html
    assert "Annual Debt Trend" in html
    assert "INCREASING" in html
    assert "Latest Revenue Growth" in html
    assert "Latest Earnings Growth" in html
    assert "YAHOO VALUATION" in html
    assert "YAHOO FUNDAMENTALS" in html


def test_flask_stock_research_route(
    monkeypatch,
):
    import mobile_dashboard.app as dashboard_app

    received = []

    def fake_builder(symbol):
        received.append(
            symbol
        )

        return sample_report()

    monkeypatch.setattr(
        dashboard_app,
        "build_stock_research_report",
        fake_builder,
    )

    client = (
        dashboard_app.app.test_client()
    )

    response = client.get(
        "/stock-research?symbol=DOL"
    )

    assert response.status_code == 200

    assert received == [
        "DOL"
    ]

    text = response.get_data(
        as_text=True
    )

    assert "DOL.TO" in text
    assert "Northstar Stock Research" in text
