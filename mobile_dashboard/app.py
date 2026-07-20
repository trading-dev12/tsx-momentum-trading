"""
Northstar Quant Research & Trading Platform

Provides a read-only browser dashboard for monitoring the
paper-trading system.

The dashboard reads persistent project state but does not
modify trading data.
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify

from paper_trading.portfolio import PaperPortfolio


app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PORTFOLIO_STATE_FILE = (
    PROJECT_ROOT / "paper_portfolio_state.json"
)
PENDING_TRADES_FILE = (
    PROJECT_ROOT / "pending_trades.csv"
)
AUTOMATIC_EOD_STATE_FILE = (
    PROJECT_ROOT / "automatic_eod_state.json"
)
VALIDATION_REPORTS_FOLDER = (
    PROJECT_ROOT / "validation_reports"
)
LATEST_PRICES_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "latest_prices.json"
)


@app.get("/manifest.json")
def manifest():
    return jsonify(
        {
            "id": "/",
            "name": "Northstar Quant",
            "short_name": "Northstar",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#10141b",
            "theme_color": "#10141b",
            "icons": [
                {
                    "src": "/static/northstar-quant-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": "/static/northstar-quant-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
    )

@app.get("/service-worker.js")
def service_worker():



    javascript = """
const CACHE_NAME = "northstar-quant-v2";

self.addEventListener("install", function(event) {
    self.skipWaiting();
});

self.addEventListener("activate", function(event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", function(event) {
    event.respondWith(
        fetch(event.request)
    );
});
"""

    response = app.response_class(
        response=javascript,
        status=200,
        mimetype="application/javascript",
    )

    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"

    return response

def load_portfolio_data(current_prices=None):
    """
    Load current portfolio information in read-only fashion.
    """

    portfolio = PaperPortfolio(
        state_file=str(PORTFOLIO_STATE_FILE),
    )

    return {
    "summary": portfolio.summary(current_prices),
    "open_positions": list(
        portfolio.open_positions
    ),
    "closed_trades": list(
        portfolio.closed_trades
    ),
}

def load_latest_prices():
    """
    Load the latest read-only price snapshot.
    """

    price_snapshot = load_json_file(
        LATEST_PRICES_FILE
    )

    return {
        "generated_at": price_snapshot.get(
            "generated_at",
            "--",
        ),
        "prices": price_snapshot.get(
            "prices",
            {},
        ),
    }
def load_json_file(file_path):
    """
    Load a JSON file without modifying it.
    """

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_latest_validation_report():
    """
    Return the newest pipeline-validation report.
    """

    report_files = list(
        VALIDATION_REPORTS_FOLDER.rglob(
            "*_pipeline_validation.json"
        )
    )

    if not report_files:
        return None

    latest_report_file = max(
        report_files,
        key=lambda path: path.stat().st_mtime,
    )

    report = load_json_file(
        latest_report_file
    )

    return {
        "file_path": latest_report_file,
        "report": report,
    }


def file_status(file_path):
    """
    Return whether a required persistent file exists.
    """

    if file_path.exists():
        return {
            "status": "PASS",
            "text": "AVAILABLE",
        }

    return {
        "status": "FAIL",
        "text": "MISSING",
    }


def status_class(status):
    """
    Map a system status to a CSS class.
    """

    normalized_status = str(status).upper()

    if normalized_status == "PASS":
        return "health-pass"

    if normalized_status == "WARNING":
        return "health-warning"

    return "health-fail"


@app.get("/")
def dashboard():
    """
    Display the read-only Trade Control Center.
    """

    try:
        latest_price_data = load_latest_prices()

        current_prices = latest_price_data[
            "prices"
    ]

        portfolio_data = load_portfolio_data(
            current_prices
    )

        prices_generated_at = latest_price_data[
            "generated_at"
        ]

        summary = portfolio_data["summary"]

        open_positions = portfolio_data[
            "open_positions"
        ]

        closed_trades = portfolio_data[
            "closed_trades"
        ]

        data_status = "LIVE DATA AVAILABLE"
        error_message = ""

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        summary = {
            "starting_cash": 0.0,
            "cash": 0.0,
            "open_position_value": 0.0,
            "portfolio_exposure": 0.0,
            "portfolio_value": 0.0,
            "total_return": 0.0,
            "open_positions": 0,
            "closed_trades": 0,
        }

        open_positions = []
        closed_trades = []

        data_status = "PORTFOLIO DATA UNAVAILABLE"
        error_message = str(error)

    portfolio_file_health = file_status(
        PORTFOLIO_STATE_FILE
    )

    pending_file_health = file_status(
        PENDING_TRADES_FILE
    )

    eod_file_health = file_status(
        AUTOMATIC_EOD_STATE_FILE
    )

    try:
        eod_state = load_json_file(
            AUTOMATIC_EOD_STATE_FILE
        )

        last_eod_date = eod_state.get(
            "last_run_date",
            "--",
        )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        last_eod_date = "--"

    try:
        validation_result = (
            load_latest_validation_report()
        )

        if validation_result is None:
            validation_status = "WARNING"
            validation_generated_at = "--"
            validation_summary = {
                "pass_count": 0,
                "warning_count": 0,
                "fail_count": 0,
                "pending_trades": 0,
            }

        else:
            validation_report = (
                validation_result["report"]
            )

            validation_status = (
                validation_report.get(
                    "overall_status",
                    "WARNING",
                )
            )

            validation_generated_at = (
                validation_report.get(
                    "generated_at",
                    "--",
                )
            )

            validation_summary = (
                validation_report.get(
                    "summary",
                    {},
                )
            )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        validation_status = "FAIL"
        validation_generated_at = "--"
        validation_summary = {
            "pass_count": 0,
            "warning_count": 0,
            "fail_count": 0,
            "pending_trades": 0,
        }

    position_rows = []

    total_open_pl = 0.0
    total_open_pl_display = "$0.00"

    for position in open_positions:
        entry_price = float(
            position.get("entry_price", 0)
        )

        shares = int(
            position.get("shares", 0)
        )

        stop_price = float(
            position.get("stop_price", 0)
        )

        target_price = float(
            position.get("target_price", 0)
        )

        symbol = position.get(
            "symbol",
            "--",
        )

        current_price = float(
            current_prices.get(
                symbol,
                entry_price,
            )
        )

        position_value = current_price * shares
     
        open_pl = (
            current_price - entry_price
        ) * shares

        total_open_pl += open_pl

        open_pl_display = (
            f"-${abs(open_pl):,.2f}"
            if open_pl < 0
            else f"${open_pl:,.2f}"
        )

        open_pl_color = (
             "#198754"
            if open_pl > 0
            else "#dc3545"
            if open_pl < 0
            else "#6c757d"
        )

        position_rows.append(
            f"""
            <tr>
                <td>
                    <strong>
                        {position.get("symbol", "--")}
                    </strong>
                </td>

                <td>
                    {position.get("strategy", "--")}
                </td>

                <td>
                    {position.get("entry_date", "--")}
                </td>

                 <td>
                    ${entry_price:,.2f}
                </td>

                <td>
                    ${current_price:,.2f}
                </td>

                <td style="color: {open_pl_color}; font-weight: bold;">
                    {open_pl_display}
                </td>

                <td>
                    {shares}
                </td>

                <td>
                    ${stop_price:,.2f}
                </td>

                <td>
                    ${target_price:,.2f}
                </td>

                <td>
                    ${position_value:,.2f}
                </td>
            </tr>
            """
        )

        total_open_pl_display = (
            f"-${abs(total_open_pl):,.2f}"
            if total_open_pl < 0
            else f"${total_open_pl:,.2f}"
        )

    total_open_pl_color = (
            "#198754"
            if total_open_pl > 0
            else "#dc3545"
            if total_open_pl < 0
            else "#ffffff"
        )

    realized_pl = sum(
        float(trade.get("profit_loss", 0) or 0)
        for trade in closed_trades
    )

    realized_pl_display = (
        f"-${abs(realized_pl):,.2f}"
        if realized_pl < 0
        else f"${realized_pl:,.2f}"
    )

    realized_pl_color = (
        "#198754"
        if realized_pl > 0
        else "#dc3545"
        if realized_pl < 0
        else "#ffffff"
    )

    if position_rows:
        open_positions_html = "".join(
            position_rows
        )
    else:
        open_positions_html = """
        <tr>
            <td colspan="10">
                No open positions.
            </td>
        </tr>
        """

    refreshed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )    

    return f"""
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

        <title>Northstar Quant</title>

        <link
            rel="icon"
            type="image/png"
            href="/static/northstar-quant-192.png"
        >

        <link
            rel="apple-touch-icon"
            href="/static/northstar-quant-512.png"
        >

        <meta
            name="theme-color"
            content="#10141b"
        >

        <meta name="mobile-web-app-capable" content="yes">

        <meta name="apple-mobile-web-app-capable" content="yes">

        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

        <meta name="apple-mobile-web-app-title" content="Northstar Quant">

        <link rel="manifest" href="/manifest.json">

        <style>
            * {{
                box-sizing: border-box;
            }}
            

            body {{
                margin: 0;
                padding: 24px;
                background: #10141b;
                color: #f4f7fa;
                font-family: Arial, sans-serif;
            }}

            .container {{
    max-width: 1000px;
    margin: 0 auto;
}}

.dashboard-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}}

.branding {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.logo {{
    width: 52px;
    height: 52px;
    object-fit: contain;
    flex-shrink: 0;
}}

.branding h1 {{
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
}}

.subtitle {{
    color: #9ca3af;
    font-size: 0.85rem;
    margin-top: 2px;
}}

.paper-badge {{
    background: #f59e0b;
    color: #111827;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
}}
            .status-card,
            .health-card,
            .table-card {{
                margin-top: 20px;
                padding: 20px;
                background: #1b2230;
                border: 1px solid #303a4c;
                border-radius: 12px;
            }}

            .status {{
                font-size: 18px;
                font-weight: bold;
            }}

            .grid {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(160px, 1fr));
                gap: 14px;
                margin-top: 20px;
            }}

            .metric {{
                padding: 18px;
                background: #1b2230;
                border: 1px solid #303a4c;
                border-radius: 12px;
            }}

            .metric-label {{
                color: #aeb8c8;
                font-size: 13px;
                text-transform: uppercase;
            }}

            .metric-value {{
                margin-top: 8px;
                font-size: 24px;
                font-weight: bold;
            }}

            .health-card h2,
            .table-card h2 {{
                margin-top: 0;
                margin-bottom: 16px;
                font-size: 20px;
            }}

            .health-grid {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
            }}

            .health-item {{
                padding: 14px;
                background: #151b26;
                border: 1px solid #303a4c;
                border-radius: 10px;
            }}

            .health-label {{
                color: #aeb8c8;
                font-size: 12px;
                text-transform: uppercase;
            }}

            .health-value {{
                margin-top: 7px;
                font-size: 16px;
                font-weight: bold;
            }}

            .health-pass {{
                color: #7ee2a8;
            }}

            .health-warning {{
                color: #ffd479;
            }}

            .health-fail {{
                color: #ff9b9b;
            }}

            .table-card {{
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 760px;
            }}

            th,
            td {{
                padding: 12px 10px;
                border-bottom: 1px solid #303a4c;
                text-align: left;
                white-space: nowrap;
            }}

            th {{
                color: #aeb8c8;
                font-size: 12px;
                text-transform: uppercase;
            }}

            td {{
                font-size: 14px;
            }}

            tbody tr:last-child td {{
                border-bottom: none;
            }}

            .footer {{
                margin-top: 20px;
                color: #aeb8c8;
                font-size: 13px;
            }}

            .error {{
                margin-top: 12px;
                color: #ffb4b4;
            }}
        </style>
    </head>

    <body>
        <main class="container">
    <header class="dashboard-header">
        <div class="branding">
            <img
                src="/static/northstar-quant-512.png"
                alt="Northstar Quant"
                class="logo"
            >

            <div>
                <h1>Northstar Quant</h1>

                <div class="subtitle">
                    Research & Trading Platform
                </div>
            </div>
        </div>

        <div class="paper-badge">
            PAPER
        </div>
    </header>

            <section class="status-card">
                <div class="status">
                    {data_status}
                </div>

                <div class="footer">
                    Read-only monitoring. No trading controls
                    are enabled.
                </div>

                {
                    f'<div class="error">{error_message}</div>'
                    if error_message
                    else ""
                }
            </section>

            

            <section class="grid">
                <div class="metric">
                    <div class="metric-label">
                        Portfolio Value
                    </div>

                    <div class="metric-value">
                        ${summary["portfolio_value"]:,.2f}
                    </div>
                </div>
                <div class="metric">
    <div class="metric-label">
        Realized P/L
    </div>

    <div
        class="metric-value"
        style="color: {realized_pl_color};"
    >
        {realized_pl_display}
    </div>
</div>
                <div class="metric">
                    <div class="metric-label">
                        Total Open P/L
                    </div>

                    <div
                        class="metric-value"
                        style="color: {total_open_pl_color};"
                    >
                        {total_open_pl_display}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Cash
                    </div>

                    <div class="metric-value">
                        ${summary["cash"]:,.2f}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Exposure
                    </div>

                    <div class="metric-value">
                        {summary["portfolio_exposure"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Total Return
                    </div>

                    <div class="metric-value">
                        {summary["total_return"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Open Positions
                    </div>

                    <div class="metric-value">
                        {summary["open_positions"]}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Closed Trades
                    </div>

                    <div class="metric-value">
                        {summary["closed_trades"]}
                    </div>
                </div>
            </section>

            <section class="table-card">
                <h2>Open Positions</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Strategy</th>
                            <th>Entry Date</th>
                            <th>Entry</th>
                            <th>Current</th>
                            <th>Open P/L</th>
                            <th>Shares</th>
                            <th>Stop</th>
                            <th>Target</th>
                            <th>Position Value</th>
                        </tr>
                    </thead>

                    <tbody>
                        {open_positions_html}
                    </tbody>
                </table>
            </section>

            <section class="health-card">
                <h2>System Health</h2>

                <div class="health-grid">
                    <div class="health-item">
                        <div class="health-label">
                            Portfolio State
                        </div>

                        <div class="
                            health-value
                            {status_class(
                                portfolio_file_health["status"]
                            )}
                        ">
                            {portfolio_file_health["text"]}
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Automatic EOD State
                        </div>

                        <div class="
                            health-value
                            {status_class(
                                eod_file_health["status"]
                            )}
                        ">
                            {eod_file_health["text"]}
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Last Automatic EOD
                        </div>

                        <div class="health-value">
                            {last_eod_date}
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Pipeline Validation
                        </div>

                        <div class="
                            health-value
                            {status_class(validation_status)}
                        ">
                            {validation_status}
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Validation Generated
                        </div>

                        <div class="health-value">
                            {validation_generated_at}
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Validation Checks
                        </div>

                        <div class="health-value">
                            {
                                validation_summary.get(
                                    "pass_count",
                                    0,
                                )
                            } pass /
                            {
                                validation_summary.get(
                                    "warning_count",
                                    0,
                                )
                            } warning /
                            {
                                validation_summary.get(
                                    "fail_count",
                                    0,
                                )
                            } fail
                        </div>
                    </div>

                    <div class="health-item">
                        <div class="health-label">
                            Pending Trades
                        </div>

                        <div class="health-value">
                            {
                                validation_summary.get(
                                    "pending_trades",
                                    0,
                                )
                            }
                        </div>
                    </div>
                </div>

                <div class="footer">
                    Scanner-running status is not shown yet
                    because no persistent scanner heartbeat
                    currently exists.
                </div>
            </section>

            <div class="footer">
                Dashboard refreshed: {refreshed_at}
                · Auto-refreshes every 60 seconds
            </div>
    <script>
            if ("serviceWorker" in navigator) {{
                window.addEventListener(
                    "load",
                    function() {{
                        navigator.serviceWorker
                            .register("/service-worker.js")
                            .catch(function(error) {{
                                console.error(
                                    "Service worker registration failed:",
                                    error
                                );
                            }});
                    }}
                );
            }}
        </script>  
    </body>
    </html>    
    """


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )