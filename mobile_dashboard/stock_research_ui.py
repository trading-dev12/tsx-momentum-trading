"""
Northstar Quant
On-Demand Stock Research Mobile UI

Provides:
- a ticker search box on the main dashboard
- a phone-friendly stock research results page

Research only. No trading state is modified.
"""

from html import escape


STOCK_RESEARCH_FORM_HTML = """
<section
    id="stock-research-search"
    style="
        max-width: 1000px;
        margin: 14px auto 18px auto;
        padding: 16px;
        background: #1b2230;
        border: 1px solid #303a4c;
        border-radius: 12px;
        font-family: Arial, sans-serif;
        color: #f4f7fa;
    "
>
    <div
        style="
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        "
    >
        Stock Research
    </div>

    <div
        style="
            color: #aeb8c8;
            font-size: 13px;
            margin-bottom: 12px;
        "
    >
        Analyze any TSX ticker. Research only ? no trade will be created.
    </div>

    <form
        action="/stock-research"
        method="get"
        style="
            display: flex;
            gap: 8px;
            width: 100%;
        "
    >
        <input
            type="text"
            name="symbol"
            placeholder="DOL.TO"
            maxlength="20"
            autocomplete="off"
            autocapitalize="characters"
            spellcheck="false"
            required
            style="
                flex: 1;
                min-width: 0;
                padding: 12px 13px;
                border-radius: 8px;
                border: 1px solid #465269;
                background: #10141b;
                color: #ffffff;
                font-size: 16px;
            "
        >

        <button
            type="submit"
            style="
                padding: 12px 16px;
                border: 0;
                border-radius: 8px;
                background: #2563eb;
                color: #ffffff;
                font-size: 15px;
                font-weight: bold;
                cursor: pointer;
            "
        >
            Analyze
        </button>
    </form>
</section>
"""


def inject_stock_research_form(html):
    """
    Insert the research form immediately after the body tag.
    """

    if not isinstance(
        html,
        str,
    ):
        return html

    if (
        'id="stock-research-search"'
        in html
    ):
        return html

    body_tag = "<body>"

    if body_tag not in html:
        return html

    return html.replace(
        body_tag,
        (
            body_tag
            + STOCK_RESEARCH_FORM_HTML
        ),
        1,
    )


def _text(value, default="--"):
    if value in (
        None,
        "",
    ):
        return default

    return escape(
        str(value)
    )


def _number(
    value,
    decimals=2,
    suffix="",
):
    try:
        return (
            f"{float(value):,.{decimals}f}"
            f"{suffix}"
        )
    except (
        TypeError,
        ValueError,
    ):
        return "--"


def _money(value):
    try:
        return (
            f"${float(value):,.2f}"
        )
    except (
        TypeError,
        ValueError,
    ):
        return "--"


def _metric(
    label,
    value,
):
    return f"""
    <div class="metric">
        <div class="label">
            {escape(str(label))}
        </div>

        <div class="value">
            {value}
        </div>
    </div>
    """


def _status_message(
    component,
):
    status = str(
        component.get(
            "status",
            "UNAVAILABLE",
        )
    ).upper()

    if status == "AVAILABLE":
        return ""

    reason = _text(
        component.get(
            "reason",
            "",
        ),
        "Data unavailable.",
    )

    return f"""
    <div class="component-warning">
        {reason}
    </div>
    """


def render_stock_research_page(
    report=None,
    query="",
    error="",
):
    """
    Render the read-only arbitrary-stock research page.
    """

    query_display = escape(
        str(query or "")
    )

    if report:
        symbol = _text(
            report.get(
                "symbol",
                "--",
            )
        )

        overall_status = _text(
            report.get(
                "status",
                "--",
            )
        )

        measurement_date = _text(
            report.get(
                "measurement_date",
                "--",
            )
        )

        quote = report.get(
            "quote",
            {},
        )

        market = report.get(
            "market_regime",
            {},
        )

        relative = report.get(
            "relative_strength",
            {},
        )

        moving = report.get(
            "moving_average",
            {},
        )

        volatility = report.get(
            "volatility",
            {},
        )

        results_html = f"""
        <section class="section">
            <div class="symbol-row">
                <div>
                    <h1>{symbol}</h1>

                    <div class="subtitle">
                        Northstar Stock Research
                    </div>
                </div>

                <div class="status-pill">
                    {overall_status}
                </div>
            </div>

            <div class="as-of">
                Measurement date:
                {measurement_date}
            </div>
        </section>

        <section class="section">
            <h2>Market Quote</h2>

            <div class="grid">
                {_metric(
                    "Price",
                    _money(
                        quote.get(
                            "price"
                        )
                    ),
                )}

                {_metric(
                    "Bid",
                    _money(
                        quote.get(
                            "bid"
                        )
                    ),
                )}

                {_metric(
                    "Ask",
                    _money(
                        quote.get(
                            "ask"
                        )
                    ),
                )}

                {_metric(
                    "Volume",
                    _number(
                        quote.get(
                            "volume"
                        ),
                        0,
                    ),
                )}

                {_metric(
                    "Source",
                    _text(
                        quote.get(
                            "source"
                        )
                    ),
                )}
            </div>

            {_status_message(quote)}
        </section>

        <section class="section">
            <h2>Broad Market</h2>

            <div class="grid">
                {_metric(
                    "TSX Regime",
                    _text(
                        market.get(
                            "regime"
                        )
                    ),
                )}

                {_metric(
                    "XIC vs SMA 200",
                    _number(
                        market.get(
                            "close_vs_sma_200_percent"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "SMA 50 vs SMA 200",
                    _number(
                        market.get(
                            "sma_50_vs_sma_200_percent"
                        ),
                        2,
                        "%",
                    ),
                )}
            </div>

            {_status_message(market)}
        </section>

        <section class="section">
            <h2>Relative Strength</h2>

            <div class="grid">
                {_metric(
                    "20-Day Return",
                    _number(
                        relative.get(
                            "stock_return_20"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "RS vs XIC",
                    _number(
                        relative.get(
                            "rs_xic_20"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "RS vs XIU",
                    _number(
                        relative.get(
                            "rs_xiu_20"
                        ),
                        2,
                        "%",
                    ),
                )}
            </div>

            {_status_message(relative)}
        </section>

        <section class="section">
            <h2>Trend</h2>

            <div class="grid">
                {_metric(
                    "Alignment",
                    _text(
                        moving.get(
                            "trend_alignment"
                        )
                    ).replace(
                        "_",
                        " ",
                    ),
                )}

                {_metric(
                    "SMA 20",
                    _money(
                        moving.get(
                            "sma_20"
                        )
                    ),
                )}

                {_metric(
                    "SMA 50",
                    _money(
                        moving.get(
                            "sma_50"
                        )
                    ),
                )}

                {_metric(
                    "SMA 200",
                    _money(
                        moving.get(
                            "sma_200"
                        )
                    ),
                )}

                {_metric(
                    "Price vs SMA 20",
                    _number(
                        moving.get(
                            "close_vs_sma20_percent"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "Price vs SMA 200",
                    _number(
                        moving.get(
                            "close_vs_sma200_percent"
                        ),
                        2,
                        "%",
                    ),
                )}
            </div>

            {_status_message(moving)}
        </section>

        <section class="section">
            <h2>Volatility</h2>

            <div class="grid">
                {_metric(
                    "ATR 14",
                    _number(
                        volatility.get(
                            "atr_14"
                        ),
                        2,
                    ),
                )}

                {_metric(
                    "ATR %",
                    _number(
                        volatility.get(
                            "atr_percent"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "20-Day Realized Vol",
                    _number(
                        volatility.get(
                            "realized_volatility_20"
                        ),
                        2,
                        "%",
                    ),
                )}

                {_metric(
                    "Volatility Percentile",
                    _number(
                        volatility.get(
                            "volatility_percentile_252"
                        ),
                        1,
                        "%",
                    ),
                )}

                {_metric(
                    "Regime",
                    _text(
                        volatility.get(
                            "volatility_regime"
                        )
                    ),
                )}
            </div>

            {_status_message(volatility)}
        </section>
        """

    else:
        symbol = "Stock Research"
        results_html = """
        <section class="section intro">
            <h1>Stock Research</h1>

            <div class="subtitle">
                Enter any TSX-listed ticker to run
                Northstar's read-only research engine.
            </div>
        </section>
        """

    error_html = ""

    if error:
        error_html = f"""
        <div class="error">
            {escape(str(error))}
        </div>
        """

    return f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <title>
        Northstar Quant - {symbol}
    </title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 20px;
            background: #10141b;
            color: #f4f7fa;
            font-family: Arial, sans-serif;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        .top-link {{
            display: inline-block;
            margin-bottom: 16px;
            color: #9fc5ff;
            text-decoration: none;
            font-size: 14px;
        }}

        .search {{
            display: flex;
            gap: 8px;
            margin-bottom: 18px;
        }}

        .search input {{
            flex: 1;
            min-width: 0;
            padding: 13px;
            border: 1px solid #465269;
            border-radius: 8px;
            background: #151b26;
            color: #ffffff;
            font-size: 16px;
        }}

        .search button {{
            padding: 13px 17px;
            border: 0;
            border-radius: 8px;
            background: #2563eb;
            color: #ffffff;
            font-size: 15px;
            font-weight: bold;
        }}

        .section {{
            margin-top: 16px;
            padding: 18px;
            background: #1b2230;
            border: 1px solid #303a4c;
            border-radius: 12px;
        }}

        h1 {{
            margin: 0;
            font-size: 28px;
        }}

        h2 {{
            margin: 0 0 14px 0;
            font-size: 19px;
        }}

        .subtitle,
        .as-of {{
            margin-top: 6px;
            color: #aeb8c8;
        }}

        .as-of {{
            font-size: 13px;
        }}

        .symbol-row {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
        }}

        .status-pill {{
            padding: 6px 10px;
            border-radius: 999px;
            background: #26354d;
            color: #9fc5ff;
            font-size: 12px;
            font-weight: bold;
        }}

        .grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(135px, 1fr)
                );
            gap: 10px;
        }}

        .metric {{
            padding: 13px;
            background: #151b26;
            border: 1px solid #303a4c;
            border-radius: 9px;
        }}

        .label {{
            color: #aeb8c8;
            font-size: 11px;
            text-transform: uppercase;
        }}

        .value {{
            margin-top: 6px;
            font-size: 18px;
            font-weight: bold;
            overflow-wrap: anywhere;
        }}

        .component-warning {{
            margin-top: 12px;
            padding: 10px;
            background: #332b16;
            border-radius: 8px;
            color: #ffd479;
            font-size: 12px;
        }}

        .error {{
            margin-bottom: 16px;
            padding: 12px;
            background: #431c21;
            border: 1px solid #79323a;
            border-radius: 8px;
            color: #ffb3bb;
        }}

        .notice {{
            margin-top: 18px;
            color: #7f8a9d;
            font-size: 12px;
            line-height: 1.5;
        }}

        @media (max-width: 520px) {{
            body {{
                padding: 14px;
            }}

            .search button {{
                padding-left: 13px;
                padding-right: 13px;
            }}

            .grid {{
                grid-template-columns:
                    repeat(
                        2,
                        minmax(0, 1fr)
                    );
            }}

            .value {{
                font-size: 16px;
            }}
        }}
    </style>
</head>

<body>
    <main class="container">

        <a
            href="/"
            class="top-link"
        >
            ? Back to Trade Control Center
        </a>

        <form
            class="search"
            action="/stock-research"
            method="get"
        >
            <input
                type="text"
                name="symbol"
                value="{query_display}"
                placeholder="Enter TSX ticker"
                maxlength="20"
                autocomplete="off"
                autocapitalize="characters"
                spellcheck="false"
                required
            >

            <button type="submit">
                Analyze
            </button>
        </form>

        {error_html}

        {results_html}

        <div class="notice">
            Northstar Stock Research is observational and read-only.
            It does not add symbols to the scanner universe,
            create signals, queue trades, change strategy rules,
            or modify the 200-trade validation samples.
        </div>

    </main>
</body>
</html>
"""


__all__ = [
    "inject_stock_research_form",
    "render_stock_research_page",
]
