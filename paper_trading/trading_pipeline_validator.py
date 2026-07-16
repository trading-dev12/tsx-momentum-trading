from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_PORTFOLIO_FILE = Path("paper_portfolio_state.json")
DEFAULT_JOURNAL_FILE = Path("paper_trade_journal.csv")
DEFAULT_PENDING_FILE = Path("pending_trades.csv")
DEFAULT_EOD_STATE_FILE = Path("automatic_eod_state.json")
DEFAULT_VALIDATION_REPORTS_DIR = Path("validation_reports")
REPORT_VERSION = "1.0"


@dataclass
class ValidationResult:
    name: str
    status: str
    message: str


@dataclass
class ValidationReport:
    results: list[ValidationResult] = field(default_factory=list)

    def add_pass(self, name: str, message: str) -> None:
        self.results.append(ValidationResult(name, "PASS", message))

    def add_warning(self, name: str, message: str) -> None:
        self.results.append(ValidationResult(name, "WARNING", message))

    def add_fail(self, name: str, message: str) -> None:
        self.results.append(ValidationResult(name, "FAIL", message))

    @property
    def overall_status(self) -> str:
        statuses = {result.status for result in self.results}

        if "FAIL" in statuses:
            return "FAIL"

        if "WARNING" in statuses:
            return "WARNING"

        return "PASS"

    def print_report(self) -> None:
        print()
        print("=" * 72)
        print("TRADING PIPELINE VALIDATION")
        print("=" * 72)

        for result in self.results:
            print(f"{result.name:<30} {result.status:<8} {result.message}")

        print("-" * 72)
        print(f"{'OVERALL STATUS':<30} {self.overall_status}")
        print("=" * 72)


def load_portfolio(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Portfolio state must contain a JSON object.")

    return data


def load_journal(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def numbers_match(
    first: Any,
    second: Any,
    *,
    tolerance: float = 0.0001,
) -> bool:
    try:
        first_number = float(first)
        second_number = float(second)
    except (TypeError, ValueError):
        return False

    return math.isclose(
        first_number,
        second_number,
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def trade_identity(trade: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(trade.get("symbol", "")).strip(),
        str(trade.get("entry_date", "")).strip(),
        str(trade.get("exit_date", "")).strip(),
        int(float(trade.get("shares", 0))),
    )


def validate_portfolio_structure(
    portfolio: dict[str, Any],
    report: ValidationReport,
) -> None:
    required_fields = {
        "starting_cash",
        "cash",
        "open_positions",
        "closed_trades",
    }

    missing_fields = sorted(required_fields - portfolio.keys())

    if missing_fields:
        report.add_fail(
            "Portfolio structure",
            f"Missing fields: {', '.join(missing_fields)}",
        )
        return

    if not isinstance(portfolio["open_positions"], list):
        report.add_fail(
            "Portfolio structure",
            "open_positions is not a list.",
        )
        return

    if not isinstance(portfolio["closed_trades"], list):
        report.add_fail(
            "Portfolio structure",
            "closed_trades is not a list.",
        )
        return

    try:
        float(portfolio["starting_cash"])
        float(portfolio["cash"])
    except (TypeError, ValueError):
        report.add_fail(
            "Portfolio structure",
            "Cash fields are not numeric.",
        )
        return

    report.add_pass(
        "Portfolio structure",
        "Portfolio JSON contains the required fields.",
    )


def validate_open_position_duplicates(
    open_positions: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    symbols = [
        str(position.get("symbol", "")).strip()
        for position in open_positions
        if str(position.get("symbol", "")).strip()
    ]

    duplicate_symbols = sorted(
        symbol
        for symbol, count in Counter(symbols).items()
        if count > 1
    )

    if duplicate_symbols:
        report.add_fail(
            "Open-position duplicates",
            f"Duplicate symbols: {', '.join(duplicate_symbols)}",
        )
    else:
        report.add_pass(
            "Open-position duplicates",
            f"No duplicates across {len(open_positions)} open positions.",
        )


def validate_closed_trade_duplicates(
    closed_trades: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    identities = [trade_identity(trade) for trade in closed_trades]
    duplicate_trades = [
        identity
        for identity, count in Counter(identities).items()
        if count > 1
    ]

    if duplicate_trades:
        formatted = "; ".join(
            f"{symbol} {entry_date} to {exit_date}, {shares} shares"
            for symbol, entry_date, exit_date, shares in duplicate_trades
        )
        report.add_fail("Closed-trade duplicates", formatted)
    else:
        report.add_pass(
            "Closed-trade duplicates",
            f"No duplicates across {len(closed_trades)} closed trades.",
        )


def validate_cash_reconciliation(
    portfolio: dict[str, Any],
    report: ValidationReport,
) -> None:
    starting_cash = float(portfolio["starting_cash"])
    actual_cash = float(portfolio["cash"])

    open_position_cost = sum(
        float(position["entry_price"]) * int(position["shares"])
        for position in portfolio["open_positions"]
    )

    realized_profit_loss = sum(
        float(trade["profit_loss"])
        for trade in portfolio["closed_trades"]
    )

    expected_cash = (
        starting_cash
        - open_position_cost
        + realized_profit_loss
    )

    difference = actual_cash - expected_cash

    if math.isclose(actual_cash, expected_cash, abs_tol=0.01):
        report.add_pass(
            "Cash reconciliation",
            (
                f"Actual ${actual_cash:,.2f}; "
                f"expected ${expected_cash:,.2f}."
            ),
        )
    else:
        report.add_fail(
            "Cash reconciliation",
            (
                f"Actual ${actual_cash:,.2f}; "
                f"expected ${expected_cash:,.2f}; "
                f"difference ${difference:,.2f}."
            ),
        )


def find_matching_journal_rows(
    trade: dict[str, Any],
    journal_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    expected_identity = trade_identity(trade)

    return [
        row
        for row in journal_rows
        if trade_identity(row) == expected_identity
    ]


def compare_trade_to_journal_row(
    trade: dict[str, Any],
    journal_row: dict[str, str],
) -> list[str]:
    differences: list[str] = []

    numeric_fields = [
        "entry_price",
        "exit_price",
        "shares",
        "stop_price",
        "target_price",
        "tmqs",
        "rvol",
        "profit_loss",
        "profit_loss_percent",
    ]

    text_fields = [
        "symbol",
        "entry_date",
        "exit_date",
        "exit_reason",
    ]

    for field_name in numeric_fields:
        if not numbers_match(
            trade.get(field_name),
            journal_row.get(field_name),
        ):
            differences.append(field_name)

    for field_name in text_fields:
        portfolio_value = str(trade.get(field_name, "")).strip()
        journal_value = str(journal_row.get(field_name, "")).strip()

        if portfolio_value != journal_value:
            differences.append(field_name)

    return differences


def validate_closed_trades_against_journal(
    closed_trades: list[dict[str, Any]],
    journal_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    missing_trades: list[str] = []
    duplicate_matches: list[str] = []
    mismatched_trades: list[str] = []

    for trade in closed_trades:
        symbol = str(trade.get("symbol", "UNKNOWN"))
        matches = find_matching_journal_rows(trade, journal_rows)

        if not matches:
            missing_trades.append(symbol)
            continue

        if len(matches) > 1:
            duplicate_matches.append(symbol)
            continue

        differences = compare_trade_to_journal_row(trade, matches[0])

        if differences:
            mismatched_trades.append(
                f"{symbol}: {', '.join(differences)}"
            )

    if missing_trades:
        report.add_fail(
            "Journal completeness",
            f"Missing journal rows: {', '.join(missing_trades)}",
        )
    else:
        report.add_pass(
            "Journal completeness",
            f"All {len(closed_trades)} closed trades were found.",
        )

    if duplicate_matches:
        report.add_fail(
            "Journal match duplicates",
            f"Multiple matching rows: {', '.join(duplicate_matches)}",
        )
    else:
        report.add_pass(
            "Journal match duplicates",
            "Each closed trade has no more than one matching row.",
        )

    if mismatched_trades:
        report.add_fail(
            "Journal field matching",
            "; ".join(mismatched_trades),
        )
    else:
        report.add_pass(
            "Journal field matching",
            "Portfolio and journal trade fields match.",
        )


def validate_exact_journal_duplicates(
    journal_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    normalized_rows = [
        tuple(sorted((key, str(value).strip()) for key, value in row.items()))
        for row in journal_rows
    ]

    duplicate_count = sum(
        count - 1
        for count in Counter(normalized_rows).values()
        if count > 1
    )

    if duplicate_count:
        report.add_warning(
            "Historical journal duplicates",
            f"Detected {duplicate_count} exact duplicate row(s).",
        )
    else:
        report.add_pass(
            "Historical journal duplicates",
            "No exact duplicate journal rows detected.",
        )

def load_pending_trades(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_eod_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Automatic EOD state must contain a JSON object.")

    return data


def validate_pending_trade_structure(
    pending_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    required_fields = {
        "symbol",
        "signal_date",
        "signal_close",
        "atr",
        "tmqs",
        "rvol",
        "breakout",
        "reason",
        "status",
    }

    malformed_rows: list[str] = []

    for row_number, row in enumerate(pending_rows, start=2):
        missing_fields = required_fields - row.keys()

        if missing_fields:
            malformed_rows.append(
                f"row {row_number}: missing {', '.join(sorted(missing_fields))}"
            )

    if malformed_rows:
        report.add_fail(
            "Pending-trade structure",
            "; ".join(malformed_rows),
        )
    else:
        report.add_pass(
            "Pending-trade structure",
            f"All {len(pending_rows)} pending rows have required fields.",
        )


def validate_pending_trade_values(
    pending_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    issues: list[str] = []

    for row_number, row in enumerate(pending_rows, start=2):
        symbol = str(row.get("symbol", "")).strip()
        signal_date = str(row.get("signal_date", "")).strip()
        breakout = str(row.get("breakout", "")).strip()
        status = str(row.get("status", "")).strip()

        if not symbol:
            issues.append(f"row {row_number}: blank symbol")

        if not signal_date:
            issues.append(f"row {row_number}: blank signal_date")

        if not breakout:
            issues.append(f"row {row_number}: blank breakout")

        if status != "PENDING":
            issues.append(
                f"row {row_number} {symbol or 'UNKNOWN'}: "
                f"status is {status or 'blank'}"
            )

        for field_name in ("signal_close", "atr", "tmqs", "rvol"):
            try:
                value = float(row.get(field_name, ""))
            except (TypeError, ValueError):
                issues.append(
                    f"row {row_number} {symbol or 'UNKNOWN'}: "
                    f"{field_name} is not numeric"
                )
                continue

            if field_name in {"signal_close", "atr"} and value <= 0:
                issues.append(
                    f"row {row_number} {symbol or 'UNKNOWN'}: "
                    f"{field_name} must be positive"
                )

            if field_name == "tmqs" and not 0 <= value <= 100:
                issues.append(
                    f"row {row_number} {symbol or 'UNKNOWN'}: "
                    "tmqs is outside 0-100"
                )

            if field_name == "rvol" and value < 0:
                issues.append(
                    f"row {row_number} {symbol or 'UNKNOWN'}: "
                    "rvol cannot be negative"
                )

    if issues:
        report.add_fail(
            "Pending-trade values",
            "; ".join(issues),
        )
    else:
        report.add_pass(
            "Pending-trade values",
            "All pending-trade values are valid.",
        )


def validate_pending_trade_duplicates(
    pending_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    symbols = [
        str(row.get("symbol", "")).strip()
        for row in pending_rows
        if str(row.get("symbol", "")).strip()
    ]

    duplicates = sorted(
        symbol
        for symbol, count in Counter(symbols).items()
        if count > 1
    )

    if duplicates:
        report.add_fail(
            "Pending-trade duplicates",
            f"Duplicate symbols: {', '.join(duplicates)}",
        )
    else:
        report.add_pass(
            "Pending-trade duplicates",
            f"No duplicates across {len(pending_rows)} pending trades.",
        )


def validate_pending_against_open_positions(
    pending_rows: list[dict[str, str]],
    open_positions: list[dict[str, Any]],
    report: ValidationReport,
) -> None:
    pending_symbols = {
        str(row.get("symbol", "")).strip()
        for row in pending_rows
    }

    open_symbols = {
        str(position.get("symbol", "")).strip()
        for position in open_positions
    }

    conflicts = sorted(
        symbol
        for symbol in pending_symbols & open_symbols
        if symbol
    )

    if conflicts:
        report.add_fail(
            "Pending/open conflicts",
            (
                "Pending trades already have open positions: "
                f"{', '.join(conflicts)}"
            ),
        )
    else:
        report.add_pass(
            "Pending/open conflicts",
            "No pending symbol already has an open position.",
        )


def validate_eod_state(
    eod_state: dict[str, Any],
    pending_rows: list[dict[str, str]],
    report: ValidationReport,
) -> None:
    last_run_date = str(eod_state.get("last_run_date", "")).strip()

    if not last_run_date:
        report.add_fail(
            "Automatic EOD state",
            "last_run_date is missing or blank.",
        )
        return

    signal_dates = {
        str(row.get("signal_date", "")).strip()
        for row in pending_rows
        if str(row.get("signal_date", "")).strip()
    }

    mismatched_dates = sorted(
        signal_date
        for signal_date in signal_dates
        if signal_date != last_run_date
    )

    if mismatched_dates:
        report.add_fail(
            "EOD/pending date match",
            (
                f"EOD state is {last_run_date}; pending dates include "
                f"{', '.join(mismatched_dates)}."
            ),
        )
    else:
        report.add_pass(
            "EOD/pending date match",
            (
                f"Pending signals agree with EOD run date "
                f"{last_run_date}."
            ),
        )
def build_report_payload(
    report: ValidationReport,
    *,
    portfolio: dict[str, Any],
    journal_rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    eod_state: dict[str, Any],
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now()

    return {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "validation_date": generated_at.date().isoformat(),
        "overall_status": report.overall_status,
        "eod_last_run_date": str(
            eod_state.get("last_run_date", "")
        ).strip(),
        "summary": {
            "open_positions": len(
                portfolio.get("open_positions", [])
            ),
            "closed_trades": len(
                portfolio.get("closed_trades", [])
            ),
            "pending_trades": len(pending_rows),
            "journal_rows": len(journal_rows),
            "pass_count": sum(
                result.status == "PASS"
                for result in report.results
            ),
            "warning_count": sum(
                result.status == "WARNING"
                for result in report.results
            ),
            "fail_count": sum(
                result.status == "FAIL"
                for result in report.results
            ),
        },
        "checks": [
            {
                "name": result.name,
                "status": result.status,
                "message": result.message,
            }
            for result in report.results
        ],
    }


def create_validation_report_path(
    generated_at: datetime,
    reports_directory: Path = DEFAULT_VALIDATION_REPORTS_DIR,
) -> Path:
    year_directory = reports_directory / generated_at.strftime("%Y")
    month_directory = year_directory / generated_at.strftime("%m")

    month_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = (
        f"{generated_at.date().isoformat()}"
        "_pipeline_validation"
    )

    report_path = month_directory / f"{base_name}.json"

    if not report_path.exists():
        return report_path

    timestamp = generated_at.strftime("%H%M%S")
    numbered_path = (
        month_directory
        / f"{base_name}_{timestamp}.json"
    )

    counter = 2

    while numbered_path.exists():
        numbered_path = (
            month_directory
            / f"{base_name}_{timestamp}_{counter}.json"
        )
        counter += 1

    return numbered_path


def save_validation_report(
    report: ValidationReport,
    *,
    portfolio: dict[str, Any],
    journal_rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    eod_state: dict[str, Any],
    reports_directory: Path = DEFAULT_VALIDATION_REPORTS_DIR,
) -> Path:
    generated_at = datetime.now()

    payload = build_report_payload(
        report,
        portfolio=portfolio,
        journal_rows=journal_rows,
        pending_rows=pending_rows,
        eod_state=eod_state,
        generated_at=generated_at,
    )

    report_path = create_validation_report_path(
        generated_at,
        reports_directory,
    )

    with report_path.open(
        "x",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=4,
        )
        file.write("\n")

    return report_path        
def run_validation(
    portfolio_file: Path = DEFAULT_PORTFOLIO_FILE,
    journal_file: Path = DEFAULT_JOURNAL_FILE,
    pending_file: Path = DEFAULT_PENDING_FILE,
    eod_state_file: Path = DEFAULT_EOD_STATE_FILE,
) -> tuple[
    ValidationReport,
    dict[str, Any] | None,
    list[dict[str, str]] | None,
    list[dict[str, str]] | None,
    dict[str, Any] | None,
]:
    report = ValidationReport()

    try:
        portfolio = load_portfolio(portfolio_file)
        report.add_pass(
            "Portfolio file",
            f"Loaded {portfolio_file}.",
        )
    except Exception as error:
        report.add_fail("Portfolio file", str(error))
        return report, None, None, None, None

    try:
        journal_rows = load_journal(journal_file)
        report.add_pass(
            "Journal file",
            f"Loaded {len(journal_rows)} rows from {journal_file}.",
        )
    except Exception as error:
        report.add_fail("Journal file", str(error))
        return report, portfolio, None, None, None

    try:
        pending_rows = load_pending_trades(pending_file)
        report.add_pass(
            "Pending-trades file",
            f"Loaded {len(pending_rows)} rows from {pending_file}.",
        )
    except Exception as error:
        report.add_fail("Pending-trades file", str(error))
        return report, portfolio, journal_rows, None, None

    try:
        eod_state = load_eod_state(eod_state_file)
        report.add_pass(
            "Automatic EOD state file",
            f"Loaded {eod_state_file}.",
        )
    except Exception as error:
        report.add_fail("Automatic EOD state file", str(error))
        return report, portfolio, journal_rows, pending_rows, None

    validate_portfolio_structure(portfolio, report)

    if report.results[-1].status != "FAIL":
        validate_open_position_duplicates(
            portfolio["open_positions"],
            report,
        )

        validate_closed_trade_duplicates(
            portfolio["closed_trades"],
            report,
        )

        validate_cash_reconciliation(
            portfolio,
            report,
        )

        validate_closed_trades_against_journal(
            portfolio["closed_trades"],
            journal_rows,
            report,
        )

        validate_exact_journal_duplicates(
            journal_rows,
            report,
        )

        validate_pending_trade_structure(
            pending_rows,
            report,
        )

        validate_pending_trade_values(
            pending_rows,
            report,
        )

        validate_pending_trade_duplicates(
            pending_rows,
            report,
        )

        validate_pending_against_open_positions(
            pending_rows,
            portfolio["open_positions"],
            report,
        )

        validate_eod_state(
            eod_state,
            pending_rows,
            report,
        )

    return (
        report,
        portfolio,
        journal_rows,
        pending_rows,
        eod_state,
    )

def main() -> int:
    (
        report,
        portfolio,
        journal_rows,
        pending_rows,
        eod_state,
    ) = run_validation()

    report.print_report()

    if all(
        item is not None
        for item in (
            portfolio,
            journal_rows,
            pending_rows,
            eod_state,
        )
    ):
        report_path = save_validation_report(
            report,
            portfolio=portfolio,
            journal_rows=journal_rows,
            pending_rows=pending_rows,
            eod_state=eod_state,
        )

        print()
        print(f"Validation report saved: {report_path}")
    else:
        print()
        print(
            "Validation report was not saved because "
            "one or more source files could not be loaded."
        )

    return 1 if report.overall_status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())