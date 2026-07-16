from strategies.breakout_52week_adapter import build_breakout_52week_input


def test_adapter_maps_quote_fields():
    quote = {
        "symbol": "TEST.TO",
        "price": 50.25,
        "prior_52_week_high": 49.75,
        "average_volume": 750_000,
        "relative_volume": 1.80,
        "sma_50": 47.00,
        "sma_200": 42.00,
    }

    result = build_breakout_52week_input(quote)

    assert result.symbol == "TEST.TO"
    assert result.close == 50.25
    assert result.prior_52_week_high == 49.75
    assert result.average_volume == 750_000
    assert result.rvol == 1.80
    assert result.sma_50 == 47.00
    assert result.sma_200 == 42.00


def test_adapter_defaults_missing_values_to_zero():
    result = build_breakout_52week_input({})

    assert result.symbol == ""
    assert result.close == 0.0
    assert result.prior_52_week_high == 0.0
    assert result.average_volume == 0
    assert result.rvol == 0.0
    assert result.sma_50 == 0.0
    assert result.sma_200 == 0.0