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



def _format_optional_money(value):
    """
    Format optional money without treating missing data as zero.
    """

    if value is None:
        return "--"

    return _format_money(
        value
    )


def _format_optional_number(
    value,
    decimals=2,
    suffix="",
):
    """
    Format an optional numeric value.
    """

    if value is None:
        return "--"

    try:
        number = float(
            value
        )
    except (TypeError, ValueError):
        return "--"

    return (
        f"{number:.{decimals}f}"
        f"{suffix}"
    )


def _format_signed_number(
    value,
    decimals=2,
    suffix="",
):
    """
    Format a numeric change with an explicit sign.
    """

    if value is None:
        return "--"

    try:
        number = float(
            value
        )
    except (TypeError, ValueError):
        return "--"

    sign = (
        "+"
        if number > 0
        else ""
    )

    return (
        f"{sign}"
        f"{number:.{decimals}f}"
        f"{suffix}"
    )


def _format_signed_money(value):
    """
    Format a monetary change with an explicit sign.
    """

    if value is None:
        return "--"

    try:
        number = float(
            value
        )
    except (TypeError, ValueError):
        return "--"

    if number > 0:
        return (
            f"+${number:,.2f}"
        )

    if number < 0:
        return (
            f"-${abs(number):,.2f}"
        )

    return "$0.00"


def _candidate_stability_html(data):
    """
    Render Candidate History and Stability information.
    """

    history = data.get(
        "candidate_history",
        {},
    ) or {}

    candidates = data.get(
        "candidate_stability",
        [],
    ) or []

    raw_history_status = str(
        history.get(
            "status",
            "NO_HISTORY_YET",
        )
        or "NO_HISTORY_YET"
    )

    history_status = escape(
        raw_history_status.replace(
            "_",
            " ",
        )
    )

    observation_count = int(
        history.get(
            "observation_count",
            0,
        )
        or 0
    )

    current_count = sum(
        1
        for candidate in candidates
        if candidate.get(
            "currently_present",
            False,
        )
    )

    tracked_count = len(
        candidates
    )

    message = history.get(
        "message"
    )

    if (
        raw_history_status
        == "NO_HISTORY_YET"
    ):
        candidate_cards = """
        <div class="empty-state"
             style="margin-top: 16px;">
            No Candidate Stability history has been
            recorded yet. The first automatic EOD
            research capture will establish the
            starting observation.
        </div>
        """

    elif (
        raw_history_status
        == "UNAVAILABLE"
    ):
        detail = (
            escape(
                str(message)
            )
            if message
            else (
                "Candidate history could not be read."
            )
        )

        candidate_cards = f"""
        <div class="empty-state"
             style="margin-top: 16px;">
            Candidate Stability history is currently
            unavailable.<br>
            {detail}
        </div>
        """

    elif not candidates:
        candidate_cards = """
        <div class="empty-state"
             style="margin-top: 16px;">
            Candidate history is available, but no
            quality-gated candidate patterns have
            been tracked yet.
        </div>
        """

    else:
        cards = []

        for candidate in candidates:
            factor = escape(
                str(
                    candidate.get(
                        "factor",
                        "--",
                    )
                ).replace(
                    "_",
                    " ",
                ).title().replace(
                    "Atr ",
                    "ATR ",
                )
            )

            value = escape(
                str(
                    candidate.get(
                        "value",
                        "--",
                    )
                )
            )

            stability_status = escape(
                str(
                    candidate.get(
                        "stability_status",
                        "UNKNOWN",
                    )
                ).replace(
                    "_",
                    " ",
                )
            )

            currently_present = bool(
                candidate.get(
                    "currently_present",
                    False,
                )
            )

            presence = (
                "CURRENT"
                if currently_present
                else "DISAPPEARED"
            )

            observations = int(
                candidate.get(
                    "observation_count",
                    0,
                )
                or 0
            )

            presence_rate = float(
                candidate.get(
                    "presence_rate_percent",
                    0.0,
                )
                or 0.0
            )

            current_streak = int(
                candidate.get(
                    "current_streak",
                    0,
                )
                or 0
            )

            disappearance_count = int(
                candidate.get(
                    "disappearance_count",
                    0,
                )
                or 0
            )

            reappearance_count = int(
                candidate.get(
                    "reappearance_count",
                    0,
                )
                or 0
            )

            first_trades = int(
                candidate.get(
                    "first_trade_count",
                    0,
                )
                or 0
            )

            latest_trades = int(
                candidate.get(
                    "latest_trade_count",
                    0,
                )
                or 0
            )

            trade_change = (
                _format_signed_number(
                    candidate.get(
                        "trade_count_change"
                    ),
                    decimals=0,
                )
            )

            first_expectancy = (
                _format_optional_money(
                    candidate.get(
                        "first_expectancy"
                    )
                )
            )

            latest_expectancy = (
                _format_optional_money(
                    candidate.get(
                        "latest_expectancy"
                    )
                )
            )

            expectancy_change = (
                _format_signed_money(
                    candidate.get(
                        "expectancy_change"
                    )
                )
            )

            first_pf = (
                _format_profit_factor(
                    candidate.get(
                        "first_profit_factor"
                    )
                )
            )

            latest_pf = (
                _format_profit_factor(
                    candidate.get(
                        "latest_profit_factor"
                    )
                )
            )

            pf_change = (
                _format_signed_number(
                    candidate.get(
                        "profit_factor_change"
                    )
                )
            )

            first_win_rate = (
                _format_optional_number(
                    candidate.get(
                        "first_win_rate"
                    ),
                    suffix="%",
                )
            )

            latest_win_rate = (
                _format_optional_number(
                    candidate.get(
                        "latest_win_rate"
                    ),
                    suffix="%",
                )
            )

            win_rate_change = (
                _format_signed_number(
                    candidate.get(
                        "win_rate_change"
                    ),
                    suffix=" pts",
                )
            )

            cards.append(
                f"""
                <div
                    class="metric"
                    style="margin-top: 14px;"
                >
                    <div class="candidate-title">
                        {factor}: {value}
                    </div>

                    <div class="candidate-rating">
                        {stability_status}
                    </div>

                    <div class="status">
                        Presence: {presence}
                    </div>

                    <div class="mini-grid">
                        <div class="mini-metric">
                            <span>Observations</span>
                            <strong>
                                {observations}
                            </strong>
                        </div>

                        <div class="mini-metric">
                            <span>Presence Rate</span>
                            <strong>
                                {presence_rate:.1f}%
                            </strong>
                        </div>

                        <div class="mini-metric">
                            <span>Current Streak</span>
                            <strong>
                                {current_streak}
                            </strong>
                        </div>

                        <div class="mini-metric">
                            <span>Disappearances</span>
                            <strong>
                                {disappearance_count}
                            </strong>
                        </div>

                        <div class="mini-metric">
                            <span>Reappearances</span>
                            <strong>
                                {reappearance_count}
                            </strong>
                        </div>

                        <div class="mini-metric">
                            <span>Candidate Trades</span>
                            <strong>
                                {first_trades}
                                &rarr;
                                {latest_trades}
                            </strong>
                            <span>
                                Change: {trade_change}
                            </span>
                        </div>

                        <div class="mini-metric">
                            <span>Expectancy</span>
                            <strong>
                                {first_expectancy}
                                &rarr;
                                {latest_expectancy}
                            </strong>
                            <span>
                                Change:
                                {expectancy_change}
                            </span>
                        </div>

                        <div class="mini-metric">
                            <span>Profit Factor</span>
                            <strong>
                                {first_pf}
                                &rarr;
                                {latest_pf}
                            </strong>
                            <span>
                                Change: {pf_change}
                            </span>
                        </div>

                        <div class="mini-metric">
                            <span>Win Rate</span>
                            <strong>
                                {first_win_rate}
                                &rarr;
                                {latest_win_rate}
                            </strong>
                            <span>
                                Change:
                                {win_rate_change}
                            </span>
                        </div>
                    </div>
                </div>
                """
            )

        candidate_cards = "".join(
            cards
        )

    return f"""
        <section class="section">
            <h2>
                Candidate Stability
            </h2>

            <div class="grid">
                <div class="metric">
                    <div class="label">
                        History Status
                    </div>

                    <div class="value">
                        {history_status}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        History Observations
                    </div>

                    <div class="value">
                        {observation_count}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Tracked Patterns
                    </div>

                    <div class="value">
                        {tracked_count}
                    </div>
                </div>

                <div class="metric">
                    <div class="label">
                        Current Patterns
                    </div>

                    <div class="value">
                        {current_count}
                    </div>
                </div>
            </div>

            <div class="research-note">
                Stability is descriptive research only.
                IMPROVING, STABLE, MIXED,
                REAPPEARED, DETERIORATING, NEW,
                and DISAPPEARED describe how observed
                candidate metrics
                are changing. They do not prove an edge.
            </div>

            {candidate_cards}
        </section>
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

    stability_html = (
        _candidate_stability_html(
            data
        )
    )

    research_quality_landmark = (
        '<section class="section">\n'
        '            <h2>\n'
        '                Research Data Quality'
    )

    if research_quality_landmark in html:
        html = html.replace(
            research_quality_landmark,
            (
                stability_html
                + "\n"
                + research_quality_landmark
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
