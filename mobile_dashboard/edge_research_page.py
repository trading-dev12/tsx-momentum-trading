"""
Northstar Quant
Edge Research Dashboard Page

Read-only HTML renderer for Edge Research information.

This module never changes trading rules, signals,
positions, portfolios, pending trades, or journals.
"""

from html import escape


def _format_profit_factor(value):
    """
    Format Profit Factor for display.
    """

    if value is None:
        return "--"

    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "--"


def _format_money(value):
    """
    Format a numeric value as money.
    """

    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0

    if number < 0:
        return f"-${abs(number):,.2f}"

    return f"${number:,.2f}"


def _candidate_html(candidate):
    """
    Render the current highest-ranked research candidate.
    """

    if not candidate:
        return """
        <div class="empty-state">
            No current research candidate.
        </div>
        """

    factor = escape(
        str(
            candidate.get(
                "factor",
                "--",
            )
        ).replace(
            "_",
            " ",
        ).title()
    )

    value = escape(
        str(
            candidate.get(
                "value",
                "--",
            )
        )
    )

    rating = escape(
        str(
            candidate.get(
                "research_rating",
                "--",
            )
        ).replace(
            "_",
            " ",
        )
    )

    trades = int(
        candidate.get(
            "trade_count",
            0,
        )
        or 0
    )

    win_rate = float(
        candidate.get(
            "win_rate",
            0.0,
        )
        or 0.0
    )

    profit_factor = (
        _format_profit_factor(
            candidate.get(
                "profit_factor"
            )
        )
    )

    expectancy = (
        _format_money(
            candidate.get(
                "expectancy",
                0.0,
            )
        )
    )

    return f"""
    <div class="candidate-title">
        {factor}: {value}
    </div>

    <div class="candidate-rating">
        {rating}
    </div>

    <div class="mini-grid">
        <div class="mini-metric">
            <span>Trades</span>
            <strong>{trades}</strong>
        </div>

        <div class="mini-metric">
            <span>Win Rate</span>
            <strong>{win_rate:.2f}%</strong>
        </div>

        <div class="mini-metric">
            <span>Profit Factor</span>
            <strong>{profit_factor}</strong>
        </div>

        <div class="mini-metric">
            <span>Expectancy</span>
            <strong>{expectancy}</strong>
        </div>
    </div>

    <div class="research-note">
        This is an observed research pattern only.
        It is not a validated trading edge.
    </div>
    """


def _render_edge_research_page_base(data):
    """
    Render one complete read-only Edge Research page.
    """

    strategy = escape(
        str(
            data.get(
                "strategy",
                "Unknown",
            )
        )
    )

    notice = escape(
        str(
            data.get(
                "research_only_notice",
                "",
            )
        )
    )

    validation = data.get(
        "validation",
        {},
    )

    baseline = data.get(
        "baseline",
        {},
    )

    enrichment = data.get(
        "enrichment",
        {},
    )

    readiness = data.get(
        "combination_readiness",
        {},
    )

    quality = data.get(
        "source_quality",
        {},
    )

    candidate = data.get(
        "best_candidate"
    )

    completed = int(
        validation.get(
            "completed_trades",
            0,
        )
        or 0
    )

    validation_target = int(
        validation.get(
            "target",
            200,
        )
        or 200
    )

    validation_progress = float(
        validation.get(
            "progress_percent",
            0.0,
        )
        or 0.0
    )

    enriched = int(
        enrichment.get(
            "fully_enriched_trades",
            0,
        )
        or 0
    )

    enriched_target = int(
        enrichment.get(
            "target",
            60,
        )
        or 60
    )

    enrichment_progress = float(
        enrichment.get(
            "progress_percent",
            0.0,
        )
        or 0.0
    )

    distinct_dates = int(
        enrichment.get(
            "distinct_entry_dates",
            0,
        )
        or 0
    )

    distinct_target = int(
        enrichment.get(
            "distinct_entry_date_target",
            10,
        )
        or 10
    )

    date_progress = float(
        enrichment.get(
            "date_progress_percent",
            0.0,
        )
        or 0.0
    )

    win_rate = float(
        baseline.get(
            "win_rate",
            0.0,
        )
        or 0.0
    )

    profit_factor = (
        _format_profit_factor(
            baseline.get(
                "profit_factor"
            )
        )
    )

    expectancy = (
        _format_money(
            baseline.get(
                "expectancy",
                0.0,
            )
        )
    )

    sample_status = escape(
        str(
            baseline.get(
                "sample_status",
                "--",
            )
        ).replace(
            "_",
            " ",
        )
    )

    readiness_status = escape(
        str(
            readiness.get(
                "status",
                "--",
            )
        ).replace(
            "_",
            " ",
        )
    )

    candidate_count = int(
        data.get(
            "candidate_count",
            0,
        )
        or 0
    )

    recorded_coverage = float(
        quality.get(
            "recorded_coverage_percent",
            0.0,
        )
        or 0.0
    )

    ibkr_recorded = float(
        quality.get(
            "ibkr_percent_of_recorded",
            0.0,
        )
        or 0.0
    )

    fallback_count = int(
        quality.get(
            "fallback_source_observations",
            0,
        )
        or 0
    )

    source_status = escape(
        str(
            quality.get(
                "status",
                "--",
            )
        ).replace(
            "_",
            " ",
        )
    )

    candidate_html = (
        _candidate_html(
            candidate
        )
    )

    return f"""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >

    <meta
        http-equiv="refresh"
        content="60"
    >

    <title>
        Northstar Quant - Edge Research
    </title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 22px;
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
            margin-bottom: 18px;
            color: #9fc5ff;
            text-decoration: none;
            font-size: 14px;
        }}

        h1 {{
            margin: 0;
            font-size: 28px;
        }}

        .subtitle {{
            margin-top: 6px;
            color: #aeb8c8;
        }}

        .warning {{
            margin-top: 20px;
            padding: 16px;
            background: #332b16;
            border: 1px solid #806b2a;
            border-radius: 12px;
            color: #ffd479;
            font-weight: bold;
        }}

        .section {{
            margin-top: 20px;
            padding: 20px;
            background: #1b2230;
            border: 1px solid #303a4c;
            border-radius: 12px;
        }}

        .section h2 {{
            margin-top: 0;
            font-size: 19px;
        }}

        .grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(150px, 1fr)
                );
            gap: 12px;
        }}

        .metric {{
            padding: 15px;
            background: #151b26;
            border: 1px solid #303a4c;
            border-radius: 10px;
        }}

        .label {{
            color: #aeb8c8;
            font-size: 12px;
            text-transform: uppercase;
        }}

        .value {{
            margin-top: 7px;
            font-size: 22px;
            font-weight: bold;
        }}

        .progress {{
            height: 10px;
            margin-top: 12px;
            background: #303a4c;
            border-radius: 999px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: #7ee2a8;
        }}

        .candidate-title {{
            font-size: 21px;
            font-weight: bold;
        }}

        .candidate-rating {{
            display: inline-block;
            margin-top: 10px;
            padding: 5px 9px;
            border-radius: 999px;
            background: #2a3445;
            color: #ffd479;
            font-size: 12px;
            font-weight: bold;
        }}

        .mini-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(130px, 1fr)
                );
            gap: 10px;
            margin-top: 16px;
        }}

        .mini-metric {{
            padding: 12px;
            background: #151b26;
            border-radius: 8px;
        }}

        .mini-metric span {{
            display: block;
            color: #aeb8c8;
            font-size: 12px;
        }}

        .mini-metric strong {{
            display: block;
            margin-top: 5px;
            font-size: 17px;
        }}

        .research-note {{
            margin-top: 15px;
            color: #aeb8c8;
            font-size: 13px;
        }}

        .status {{
            margin-top: 12px;
            font-weight: bold;
        }}

        .empty-state {{
            color: #aeb8c8;
        }}

        .footer {{
            margin-top: 22px;
            color: #7f8a9d;
            font-size: 12px;
        }}
    </style>
</head>

<body>
    <main class="container">

        <a
            href="/"
            class="top-link"
        >
            ← Back to Trade Control Center
        </a>

        <h1>
            Edge Research
        </h1>

        <div class="subtitle">
            {strategy} Strategy
        </div>

        <div class="warning">
            {notice}
        </div>

        <section class="section">
            <h2>
                Validation Progress
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        Completed Trades
                    </div>

                    <div class="value">
                        {completed}/{validation_target}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Progress
                    </div>

                    <div class="value">
                        {validation_progress:.1f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Sample Status
                    </div>

                    <div class="value">
                        {sample_status}
                    </div>
                </div>
            </div>

            <div class="progress">
                <div
                    class="progress-fill"
                    style="width: {validation_progress:.2f}%;"
                ></div>
            </div>
        </section>

        <section class="section">
            <h2>
                Current Baseline
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        Win Rate
                    </div>

                    <div class="value">
                        {win_rate:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Profit Factor
                    </div>

                    <div class="value">
                        {profit_factor}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Expectancy
                    </div>

                    <div class="value">
                        {expectancy}
                    </div>
                </div>
            </div>
        </section>

        <section class="section">
            <h2>
                Research Depth
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        Fully Enriched
                    </div>

                    <div class="value">
                        {enriched}/{enriched_target}
                    </div>

                    <div class="progress">
                        <div
                            class="progress-fill"
                            style="width: {enrichment_progress:.2f}%;"
                        ></div>
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Distinct Entry Dates
                    </div>

                    <div class="value">
                        {distinct_dates}/{distinct_target}
                    </div>

                    <div class="progress">
                        <div
                            class="progress-fill"
                            style="width: {date_progress:.2f}%;"
                        ></div>
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Combination Research
                    </div>

                    <div class="value">
                        {readiness_status}
                    </div>
                </div>
            </div>
        </section>

        <section class="section">
            <h2>
                Best Current Watched Pattern
            </h2>

            {candidate_html}

            <div class="status">
                Quality-gated candidates:
                {candidate_count}
            </div>
        </section>

        <section class="section">
            <h2>
                Research Data Quality
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        Historical Source Audit
                    </div>

                    <div class="value">
                        {recorded_coverage:.1f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        IBKR of Recorded
                    </div>

                    <div class="value">
                        {ibkr_recorded:.1f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Fallback Uses
                    </div>

                    <div class="value">
                        {fallback_count}
                    </div>
                </div>
            </div>

            <div class="status">
                Source audit status:
                {source_status}
            </div>

            <div class="research-note">
                Older completed trades may have no source audit
                because source tracking was added later.
                Missing historical source records are not treated
                as Yahoo or IBKR.
            </div>
        </section>

        <div class="footer">
            Read-only research display.
            No strategy or trading controls are available here.
        </div>

    </main>
</body>
</html>
"""


def _enrichment_integrity_html(data):
    """
    Render the read-only enrichment integrity section.
    """

    integrity = data.get(
        "enrichment_integrity",
        {},
    ) or {}

    total_trades = int(
        integrity.get(
            "total_trade_count",
            0,
        )
        or 0
    )

    fully_enriched = int(
        integrity.get(
            "fully_enriched_trade_count",
            0,
        )
        or 0
    )

    coverage = float(
        integrity.get(
            "overall_coverage_percent",
            0.0,
        )
        or 0.0
    )

    monitor_start = escape(
        str(
            integrity.get(
                "monitor_start_date",
                "--",
            )
        )
    )

    monitored_trades = int(
        integrity.get(
            "monitored_trade_count",
            0,
        )
        or 0
    )

    monitored_complete = int(
        integrity.get(
            "monitored_fully_enriched_count",
            0,
        )
        or 0
    )

    monitored_incomplete = int(
        integrity.get(
            "monitored_incomplete_count",
            0,
        )
        or 0
    )

    raw_status = str(
        integrity.get(
            "integrity_status",
            "--",
        )
    )

    status_labels = {
        "NO_MONITORED_TRADES_YET": (
            "WAITING FOR NEW TRADES"
        ),
        "PASS": "PASS",
        "FAIL": "FAIL",
    }

    status = escape(
        status_labels.get(
            raw_status,
            raw_status.replace(
                "_",
                " ",
            ),
        )
    )

    return f"""
        <section class="section">
            <h2>
                Enrichment Integrity
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        Fully Enriched History
                    </div>

                    <div class="value">
                        {fully_enriched}/{total_trades}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Overall Coverage
                    </div>

                    <div class="value">
                        {coverage:.1f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Monitoring Begins
                    </div>

                    <div class="value">
                        {monitor_start}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        New Monitored Trades
                    </div>

                    <div class="value">
                        {monitored_trades}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        New Fully Enriched
                    </div>

                    <div class="value">
                        {monitored_complete}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        New Incomplete
                    </div>

                    <div class="value">
                        {monitored_incomplete}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Integrity Status
                    </div>

                    <div class="value">
                        {status}
                    </div>
                </div>
            </div>

            <div class="research-note">
                Historical incomplete trades remain legacy
                research records. Trades from the monitoring
                start date forward must satisfy the full
                enrichment requirement.
            </div>
        </section>
    """


def _strategy_selector_html(data):
    """
    Render navigation between independent strategy research pages.
    """

    current_strategy = str(
        data.get(
            "strategy",
            "",
        )
        or ""
    )

    strategies = [
        (
            "Momentum",
            "/edge-research",
        ),
        (
            "52-Week Breakout",
            "/edge-research/52-week-breakout",
        ),
        (
            "Mean Reversion",
            "/edge-research/mean-reversion",
        ),
    ]

    links = []

    for (
        strategy_name,
        href,
    ) in strategies:
        is_active = (
            current_strategy
            == strategy_name
        )

        background = (
            "#4169e1"
            if is_active
            else "#151b26"
        )

        border = (
            "#7da2ff"
            if is_active
            else "#303a4c"
        )

        links.append(
            f"""
            <a
                href="{href}"
                style="
                    display: inline-block;
                    padding: 10px 14px;
                    border-radius: 9px;
                    border: 1px solid {border};
                    background: {background};
                    color: #ffffff;
                    text-decoration: none;
                    font-weight: bold;
                "
            >
                {escape(strategy_name)}
            </a>
            """
        )

    return f"""
        <div
            style="
                display: flex;
                flex-wrap: wrap;
                gap: 9px;
                margin-top: 18px;
                margin-bottom: 4px;
            "
        >
            {''.join(links)}
        </div>
    """


def render_edge_research_page(data):
    """
    Render Edge Research with strategy navigation and
    enrichment integrity information.
    """

    html = _render_edge_research_page_base(
        data
    )

    selector_html = (
        _strategy_selector_html(
            data
        )
    )

    warning_landmark = (
        '<div class="warning">'
    )

    if warning_landmark in html:
        html = html.replace(
            warning_landmark,
            (
                selector_html
                + "\n"
                + warning_landmark
            ),
            1,
        )

    integrity_html = (
        _enrichment_integrity_html(
            data
        )
    )

    footer_landmark = (
        '<div class="footer">'
    )

    if footer_landmark not in html:
        return html

    return html.replace(
        footer_landmark,
        (
            integrity_html
            + "\n"
            + footer_landmark
        ),
        1,
    )
