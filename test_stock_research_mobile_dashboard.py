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
