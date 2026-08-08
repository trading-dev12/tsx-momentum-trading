from paper_trading.journal import (
    FIELDNAMES,
    flatten_research_into_row,
)


def test_research_data_sources_are_flattened():
    row = {}

    research = {
        "relative_strength": {
            "data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
        },
        "market_regime": {
            "data_source": "IBKR_TRADES",
        },
        "moving_average_context": {
            "data_source": "IBKR_TRADES",
        },
        "gap_analysis": {
            "data_source": "IBKR_TRADES",
        },
        "sector_strength": {
            "data_source": (
                "IBKR_ADJUSTED_LAST"
            ),
        },
        "volatility_regime": {
            "data_source": "IBKR_TRADES",
        },
    }

    result = flatten_research_into_row(
        row=row,
        research=research,
    )

    expected = {
        "rs_data_source": (
            "IBKR_ADJUSTED_LAST"
        ),
        "market_regime_data_source": (
            "IBKR_TRADES"
        ),
        "ma_data_source": (
            "IBKR_TRADES"
        ),
        "gap_data_source": (
            "IBKR_TRADES"
        ),
        "sector_strength_data_source": (
            "IBKR_ADJUSTED_LAST"
        ),
        "volatility_data_source": (
            "IBKR_TRADES"
        ),
    }

    for field, value in expected.items():
        assert field in FIELDNAMES
        assert result[field] == value
