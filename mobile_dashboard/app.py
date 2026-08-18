"""
Northstar Quant Research & Trading Platform

Provides a read-only browser dashboard for monitoring the
paper-trading system.

The dashboard reads persistent project state but does not
modify trading data.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from core.market_hours import get_tsx_market_status

from paper_trading.portfolio import PaperPortfolio
from paper_trading.dashboard import (
    calculate_position_holding_window,
)
from mobile_dashboard.edge_research_data import (
    build_edge_research_dashboard_data,
)
from mobile_dashboard.edge_research_page import (
    render_edge_research_page,
)
from mobile_dashboard.edge_research_shortcut import (
    inject_edge_research_shortcut,
)
from research.stock_research_dashboard import (
    build_stock_research_report,
)
from mobile_dashboard.stock_research_ui import (
    inject_stock_research_form,
    render_stock_research_page,
)


app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PAPER_TRADE_JOURNAL_FILE = (
    PROJECT_ROOT
    / "paper_trade_journal.csv"
)

BREAKOUT_52WEEK_TRADE_JOURNAL_FILE = (
    PROJECT_ROOT
    / "paper_trade_journal_52week.csv"
)

MEAN_REVERSION_TRADE_JOURNAL_FILE = (
    PROJECT_ROOT
    / "paper_trade_journal_mean_reversion.csv"
)

PORTFOLIO_STATE_FILE = (
    PROJECT_ROOT / "paper_portfolio_state.json"
)

BREAKOUT_52WEEK_PORTFOLIO_STATE_FILE = (
    PROJECT_ROOT / "paper_portfolio_state_52week.json"
)

MEAN_REVERSION_PORTFOLIO_STATE_FILE = (
    PROJECT_ROOT / "paper_portfolio_state_mean_reversion.json"
)

PENDING_TRADES_FILE = (
    PROJECT_ROOT / "pending_trades.csv"
)
BREAKOUT_52WEEK_PENDING_TRADES_FILE = (
    PROJECT_ROOT / "pending_trades_52week.csv"
)

MEAN_REVERSION_PENDING_TRADES_FILE = (
    PROJECT_ROOT / "pending_trades_mean_reversion.csv"
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

SCANNER_HEALTH_FILE = (
    PROJECT_ROOT
    / "data"
    / "runtime"
    / "scanner_health.json"
)


def count_pending_trades(file_path: Path) -> int:
    """
    Count rows marked PENDING in one pending-trades CSV file.
    """

    if not file_path.exists():
        return 0

    try:
        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            return sum(
                1
                for row in reader
                if str(
                    row.get("status", "")
                ).strip().upper() == "PENDING"
            )

    except (OSError, csv.Error):
        return 0
@app.after_request
def add_edge_research_shortcut_to_dashboard(
    response,
):
    """
    Add the Edge Research shortcut only to the main dashboard.
    """

    if request.path != "/":
        return response

    if response.mimetype != "text/html":
        return response

    html = response.get_data(
        as_text=True
    )

    updated_html = (
        inject_edge_research_shortcut(
            html
        )
    )

    if updated_html != html:
        response.set_data(
            updated_html
        )

    return response


@app.after_request
def add_stock_research_form_to_dashboard(
    response,
):
    """
    Add the read-only stock research form to the main dashboard.
    """

    if request.path != "/":
        return response

    if response.mimetype != "text/html":
        return response

    html = response.get_data(
        as_text=True
    )

    updated_html = (
        inject_stock_research_form(
            html
        )
    )

    if updated_html != html:
        response.set_data(
            updated_html
        )

    return response


@app.get("/stock-research")
def stock_research_dashboard():
    """
    Run read-only research for one arbitrary TSX ticker.
    """

    symbol = request.args.get(
        "symbol",
        "",
    )

    if not str(symbol).strip():
        return render_stock_research_page()

    try:
        report = (
            build_stock_research_report(
                symbol
            )
        )

    except ValueError as error:
        return (
            render_stock_research_page(
                report=None,
                query=symbol,
                error=str(error),
            ),
            400,
        )

    return render_stock_research_page(
        report=report,
        query=symbol,
    )

@app.get("/edge-research")
def edge_research_dashboard():
    """
    Display the read-only Momentum Edge Research page.
    """

    data = (
        build_edge_research_dashboard_data(
            PAPER_TRADE_JOURNAL_FILE,
            strategy_name="Momentum",
        )
    )

    return render_edge_research_page(
        data
    )


@app.get("/edge-research/52-week-breakout")
def edge_research_52week_dashboard():
    """
    Display the read-only 52-Week Breakout Edge Research page.
    """

    data = (
        build_edge_research_dashboard_data(
            BREAKOUT_52WEEK_TRADE_JOURNAL_FILE,
            strategy_name="52-Week Breakout",
        )
    )

    return render_edge_research_page(
        data
    )


@app.get("/edge-research/mean-reversion")
def edge_research_mean_reversion_dashboard():
    """
    Display the read-only Mean Reversion Edge Research page.
    """

    data = (
        build_edge_research_dashboard_data(
            MEAN_REVERSION_TRADE_JOURNAL_FILE,
            strategy_name="Mean Reversion",
        )
    )

    return render_edge_research_page(
        data
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

def load_portfolio_data(
    current_prices=None,
    state_file=PORTFOLIO_STATE_FILE,
    starting_cash=10000,
):
    """
    Load current portfolio information in read-only fashion.
    """

    portfolio = PaperPortfolio(
        starting_cash=starting_cash,
        state_file=str(state_file),
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
            "*_pipeline_validation*.json"
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
            current_prices,
        )

        breakout_52week_portfolio_data = load_portfolio_data(
            current_prices,
            state_file=BREAKOUT_52WEEK_PORTFOLIO_STATE_FILE,
            starting_cash=500000,
        )

        mean_reversion_portfolio_data = load_portfolio_data(
            current_prices,
            state_file=MEAN_REVERSION_PORTFOLIO_STATE_FILE,
            starting_cash=500000,
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

        breakout_52week_summary = (
            breakout_52week_portfolio_data["summary"]
        )

        breakout_52week_open_positions = (
            breakout_52week_portfolio_data["open_positions"]
        )

        breakout_52week_closed_trades = (
            breakout_52week_portfolio_data["closed_trades"]
        )


        mean_reversion_summary = (
            mean_reversion_portfolio_data["summary"]
        )

        mean_reversion_open_positions = (
            mean_reversion_portfolio_data["open_positions"]
        )

        mean_reversion_closed_trades = (
            mean_reversion_portfolio_data["closed_trades"]
        )

        dashboard_market_status = (
            get_tsx_market_status()
        )

        data_status = (
            "LIVE DATA AVAILABLE"
            if dashboard_market_status["is_open"]
            else (
                "LATEST MARKET DATA AVAILABLE "
                "- MARKET CLOSED"
            )
        )
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

        breakout_52week_summary = {
            "starting_cash": 0.0,
            "cash": 0.0,
            "open_position_value": 0.0,
            "portfolio_exposure": 0.0,
            "portfolio_value": 0.0,
            "total_return": 0.0,
            "open_positions": 0,
            "closed_trades": 0,
        }

        breakout_52week_open_positions = []
        breakout_52week_closed_trades = []

        mean_reversion_summary = {
            "starting_cash": 0.0,
            "cash": 0.0,
            "open_position_value": 0.0,
            "portfolio_exposure": 0.0,
            "portfolio_value": 0.0,
            "total_return": 0.0,
            "open_positions": 0,
            "closed_trades": 0,
        }

        mean_reversion_open_positions = []
        mean_reversion_closed_trades = []

        data_status = "PORTFOLIO DATA UNAVAILABLE"
        error_message = str(error)

    portfolio_file_health = file_status(
        PORTFOLIO_STATE_FILE
    )
    scanner_status = "OFFLINE"
    scanner_worker = "--"
    scanner_last_refresh = "--"
    scanner_refresh_id = "--"
    scanner_heartbeat_age_seconds = None
    scanner_session = get_tsx_market_status()

    try:
        scanner_health = load_json_file(
            SCANNER_HEALTH_FILE
        )

        scanner_worker = scanner_health.get(
            "worker",
            "--",
        )

        scanner_last_refresh = scanner_health.get(
            "last_successful_refresh",
            "--",
        )

        scanner_refresh_id = scanner_health.get(
            "refresh_id",
            "--",
        )

        heartbeat_text = scanner_health.get(
            "heartbeat",
            "",
        )

        if heartbeat_text:
            heartbeat_time = datetime.fromisoformat(
                heartbeat_text
            )

            if heartbeat_time.tzinfo is None:
                current_time = datetime.now()
            else:
                current_time = datetime.now(
                    heartbeat_time.tzinfo
                )

            scanner_heartbeat_age_seconds = max(
                0,
                int(
                    (
                        current_time
                        - heartbeat_time
                    ).total_seconds()
                ),
            )

        if not scanner_session["is_open"]:
            scanner_status = "MARKET CLOSED"

            if scanner_session["status"] == "PRE-MARKET":
                scanner_worker = "WAITING FOR MARKET OPEN"
            else:
                scanner_worker = "SLEEPING (MARKET CLOSED)"

        elif scanner_heartbeat_age_seconds is None:
            scanner_status = "OFFLINE"

        elif scanner_heartbeat_age_seconds <= 600:
            scanner_status = scanner_health.get(
                "status",
                "RUNNING",
            )

        else:
            scanner_status = "STALE"

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):

        scanner_status = "OFFLINE"
    pending_file_health = file_status(
        PENDING_TRADES_FILE
    )
    momentum_pending_count = count_pending_trades(
    PENDING_TRADES_FILE
    )

    breakout_52week_pending_count = count_pending_trades(
    BREAKOUT_52WEEK_PENDING_TRADES_FILE
    )

    mean_reversion_pending_count = count_pending_trades(
    MEAN_REVERSION_PENDING_TRADES_FILE
    )

    total_pending_count = (
        momentum_pending_count
        + breakout_52week_pending_count
        + mean_reversion_pending_count
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
    validation_summary["pending_trades"] = total_pending_count
    validation_summary["momentum_pending"] = momentum_pending_count
    validation_summary["breakout_52week_pending"] = (
        breakout_52week_pending_count
    )
    validation_summary["mean_reversion_pending"] = (
        mean_reversion_pending_count
    )

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

        holding_window = (
            calculate_position_holding_window(
                position
            )
        )

        if holding_window["available"]:
            holding_display = (
                f"{holding_window['trading_days_held']} "
                f"/ "
                f"{holding_window['max_hold_days']}"
            )

            days_left_display = str(
                holding_window[
                    "trading_days_remaining"
                ]
            )

        else:
            holding_display = "N/A"
            days_left_display = "N/A"

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
                    ${current_price:,.2f}
                </td>

                <td>
                    ${entry_price:,.2f}
                </td>

                <td style="color: {open_pl_color}; font-weight: bold;">
                    {open_pl_display}
                </td>

                <td>
                    ${stop_price:,.2f}
                </td>

                <td>
                    ${target_price:,.2f}
                </td>

                <td>
                    {days_left_display}
                </td>

                <td>
                    ${position_value:,.2f}
                </td>

                <td>
                    {shares}
                </td>

                <td>
                    {position.get("entry_date", "--")}
                </td>

                <td>
                    {holding_display}
                </td>

                <td>
                    {position.get("strategy", "--")}
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
            <td colspan="12">
                No open positions.
            </td>
        </tr>
        """

    breakout_52week_position_rows = []

    breakout_52week_total_open_pl = 0.0
    breakout_52week_total_open_pl_display = "$0.00"

    for position in breakout_52week_open_positions:
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

        holding_window = (
            calculate_position_holding_window(
                position
            )
        )

        if holding_window["available"]:
            holding_display = (
                f"{holding_window['trading_days_held']} "
                f"/ "
                f"{holding_window['max_hold_days']}"
            )

            days_left_display = str(
                holding_window[
                    "trading_days_remaining"
                ]
            )

        else:
            holding_display = "N/A"
            days_left_display = "N/A"

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

        breakout_52week_total_open_pl += open_pl

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

        breakout_52week_position_rows.append(
            f"""
            <tr>
                <td>
                    <strong>
                        {position.get("symbol", "--")}
                    </strong>
                </td>

                <td>
                    ${current_price:,.2f}
                </td>

                <td>
                    ${entry_price:,.2f}
                </td>

                <td style="color: {open_pl_color}; font-weight: bold;">
                    {open_pl_display}
                </td>

                <td>
                    ${stop_price:,.2f}
                </td>

                <td>
                    ${target_price:,.2f}
                </td>

                <td>
                    {days_left_display}
                </td>

                <td>
                    ${position_value:,.2f}
                </td>

                <td>
                    {shares}
                </td>

                <td>
                    {position.get("entry_date", "--")}
                </td>

                <td>
                    {holding_display}
                </td>

                <td>
                    {position.get("strategy", "--")}
                </td>
            </tr>
            """
        )

        breakout_52week_total_open_pl_display = (
            f"-${abs(breakout_52week_total_open_pl):,.2f}"
            if breakout_52week_total_open_pl < 0
            else f"${breakout_52week_total_open_pl:,.2f}"
        )

    breakout_52week_total_open_pl_color = (
        "#198754"
        if breakout_52week_total_open_pl > 0
        else "#dc3545"
        if breakout_52week_total_open_pl < 0
        else "#ffffff"
    )

    breakout_52week_realized_pl = sum(
        float(trade.get("profit_loss", 0) or 0)
        for trade in breakout_52week_closed_trades
    )

    breakout_52week_realized_pl_display = (
        f"-${abs(breakout_52week_realized_pl):,.2f}"
        if breakout_52week_realized_pl < 0
        else f"${breakout_52week_realized_pl:,.2f}"
    )

    breakout_52week_realized_pl_color = (
        "#198754"
        if breakout_52week_realized_pl > 0
        else "#dc3545"
        if breakout_52week_realized_pl < 0
        else "#ffffff"
    )

    if breakout_52week_position_rows:
        breakout_52week_open_positions_html = "".join(
            breakout_52week_position_rows
        )
    else:
        breakout_52week_open_positions_html = """
        <tr>
            <td colspan="12">
                No open positions.
            </td>
        </tr>
        """
    mean_reversion_position_rows = []

    mean_reversion_total_open_pl = 0.0
    mean_reversion_total_open_pl_display = "$0.00"

    for position in mean_reversion_open_positions:
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

        holding_window = (
            calculate_position_holding_window(
                position
            )
        )

        if holding_window["available"]:
            holding_display = (
                f"{holding_window['trading_days_held']} "
                f"/ "
                f"{holding_window['max_hold_days']}"
            )

            days_left_display = str(
                holding_window[
                    "trading_days_remaining"
                ]
            )

        else:
            holding_display = "N/A"
            days_left_display = "N/A"

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

        mean_reversion_total_open_pl += open_pl

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

        mean_reversion_position_rows.append(
            f"""
            <tr>
                <td>
                    <strong>
                        {position.get("symbol", "--")}
                    </strong>
                </td>

                <td>
                    ${current_price:,.2f}
                </td>

                <td>
                    ${entry_price:,.2f}
                </td>

                <td style="color: {open_pl_color}; font-weight: bold;">
                    {open_pl_display}
                </td>

                <td>
                    ${stop_price:,.2f}
                </td>

                <td>
                    ${target_price:,.2f}
                </td>

                <td>
                    {days_left_display}
                </td>

                <td>
                    ${position_value:,.2f}
                </td>

                <td>
                    {shares}
                </td>

                <td>
                    {position.get("entry_date", "--")}
                </td>

                <td>
                    {holding_display}
                </td>

                <td>
                    {position.get("strategy", "--")}
                </td>
            </tr>
            """
        )

        mean_reversion_total_open_pl_display = (
            f"-${abs(mean_reversion_total_open_pl):,.2f}"
            if mean_reversion_total_open_pl < 0
            else f"${mean_reversion_total_open_pl:,.2f}"
        )

    mean_reversion_total_open_pl_color = (
        "#198754"
        if mean_reversion_total_open_pl > 0
        else "#dc3545"
        if mean_reversion_total_open_pl < 0
        else "#ffffff"
    )

    mean_reversion_realized_pl = sum(
        float(trade.get("profit_loss", 0) or 0)
        for trade in mean_reversion_closed_trades
    )

    mean_reversion_realized_pl_display = (
        f"-${abs(mean_reversion_realized_pl):,.2f}"
        if mean_reversion_realized_pl < 0
        else f"${mean_reversion_realized_pl:,.2f}"
    )

    mean_reversion_realized_pl_color = (
        "#198754"
        if mean_reversion_realized_pl > 0
        else "#dc3545"
        if mean_reversion_realized_pl < 0
        else "#ffffff"
    )

    if mean_reversion_position_rows:
        mean_reversion_open_positions_html = "".join(
            mean_reversion_position_rows
        )
    else:
        mean_reversion_open_positions_html = """
        <tr>
            <td colspan="12">
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
                            <th>Current Price</th>
                            <th>Entry Price</th>
                            <th>Open P/L</th>
                            <th>Stop</th>
                            <th>Target</th>
                            <th>Days Left</th>
                            <th>Position Value</th>
                            <th>Shares</th>
                            <th>Entry Date</th>
                            <th>Holding</th>
                            <th>Strategy</th>
                        </tr>
                    </thead>

                    <tbody>
                        {open_positions_html}
                    </tbody>
                </table>
            </section>

            <section class="status-card">
                <h2>52-Week Breakout Strategy</h2>

                <div class="footer">
                    Independent paper-trading portfolio
                </div>
            </section>

            <section class="grid">
                <div class="metric">
                    <div class="metric-label">
                        Portfolio Value
                    </div>

                    <div class="metric-value">
                        ${breakout_52week_summary["portfolio_value"]:,.2f}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Realized P/L
                    </div>

                    <div
                        class="metric-value"
                        style="color: {breakout_52week_realized_pl_color};"
                    >
                        {breakout_52week_realized_pl_display}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Total Open P/L
                    </div>

                    <div
                        class="metric-value"
                        style="color: {breakout_52week_total_open_pl_color};"
                    >
                        {breakout_52week_total_open_pl_display}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Cash
                    </div>

                    <div class="metric-value">
                        ${breakout_52week_summary["cash"]:,.2f}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Exposure
                    </div>

                    <div class="metric-value">
                        {breakout_52week_summary["portfolio_exposure"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Total Return
                    </div>

                    <div class="metric-value">
                        {breakout_52week_summary["total_return"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Open Positions
                    </div>

                    <div class="metric-value">
                        {breakout_52week_summary["open_positions"]}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Closed Trades
                    </div>

                    <div class="metric-value">
                        {breakout_52week_summary["closed_trades"]}
                    </div>
                </div>
            </section>

            <section class="table-card">
                <h2>52-Week Breakout Open Positions</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Current Price</th>
                            <th>Entry Price</th>
                            <th>Open P/L</th>
                            <th>Stop</th>
                            <th>Target</th>
                            <th>Days Left</th>
                            <th>Position Value</th>
                            <th>Shares</th>
                            <th>Entry Date</th>
                            <th>Holding</th>
                            <th>Strategy</th>
                        </tr>
                    </thead>

                    <tbody>
                        {breakout_52week_open_positions_html}
                    </tbody>
                </table>
            </section>
             <section class="status-card">
                <h2>Mean Reversion Strategy</h2>

                <div class="footer">
                    Independent paper-trading portfolio
                </div>
            </section>

            <section class="grid">
                <div class="metric">
                    <div class="metric-label">
                        Portfolio Value
                    </div>

                    <div class="metric-value">
                        ${mean_reversion_summary["portfolio_value"]:,.2f}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Realized P/L
                    </div>

                    <div
                        class="metric-value"
                        style="color: {mean_reversion_realized_pl_color};"
                    >
                        {mean_reversion_realized_pl_display}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Total Open P/L
                    </div>

                    <div
                        class="metric-value"
                        style="color: {mean_reversion_total_open_pl_color};"
                    >
                        {mean_reversion_total_open_pl_display}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Cash
                    </div>

                    <div class="metric-value">
                        ${mean_reversion_summary["cash"]:,.2f}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Exposure
                    </div>

                    <div class="metric-value">
                        {mean_reversion_summary["portfolio_exposure"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Total Return
                    </div>

                    <div class="metric-value">
                        {mean_reversion_summary["total_return"]:.2f}%
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Open Positions
                    </div>

                    <div class="metric-value">
                        {mean_reversion_summary["open_positions"]}
                    </div>
                </div>

                <div class="metric">
                    <div class="metric-label">
                        Closed Trades
                    </div>

                    <div class="metric-value">
                        {mean_reversion_summary["closed_trades"]}
                    </div>
                </div>
            </section>

            <section class="table-card">
                <h2>Mean Reversion Open Positions</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Current Price</th>
                            <th>Entry Price</th>
                            <th>Open P/L</th>
                            <th>Stop</th>
                            <th>Target</th>
                            <th>Days Left</th>
                            <th>Position Value</th>
                            <th>Shares</th>
                            <th>Entry Date</th>
                            <th>Holding</th>
                            <th>Strategy</th>
                        </tr>
                    </thead>

                    <tbody>
                        {mean_reversion_open_positions_html}
                    </tbody>
                </table>
            </section>

            <section class="health-card">
                <h2>System Health</h2>

            <section class="status-card">


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
                            Scanner Status
                        </div>

                    <div class="
                        health-value
                        {status_class(scanner_status)}
                    ">
                        {scanner_status}
                    </div>
                </div>

                <div class="health-item">
                    <div class="health-label">
                        Last Scanner Refresh
                    </div>

                <div class="health-value">
                    {scanner_last_refresh}
                </div>
            </div>

            <div class="health-item">
                <div class="health-label">
                    Scanner Worker
                </div>

                <div class="health-value">
                    {scanner_worker}
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
                    Dashboard refreshed: {refreshed_at}
                    | Auto-refreshes every 60 seconds
                </div>

            </section>

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
