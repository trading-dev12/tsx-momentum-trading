"""
Broad TSX market regime classification.

The regime is measured using XIC.TO data available on or before the
measurement date, preventing look-ahead bias.

The calculation is shared by:
- trade research enrichment
- the Mean Reversion new-entry market guard

The regime calculation does not alter Momentum or 52-Week Breakout
strategy decisions.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any

from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK_FILE = (
    PROJECT_ROOT / "data" / "historical" / "XIC_TO.csv"
)


def _normalize_date(value: Any) -> date:
    """
    Convert a date-like value into a date object.
    """
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if value is None:
        raise ValueError("Measurement date is required.")

    text = str(value).strip()

    if not text:
        raise ValueError("Measurement date is blank.")

    return datetime.strptime(text[:10], "%Y-%m-%d").date()


def _load_adjusted_closes(
    file_path: Path,
) -> list[tuple[date, float]]:
    """
    Load date and adjusted-close values from a Yahoo Finance CSV.

    The project's Yahoo files contain a three-row header:
        Price,...
        Ticker,...
        Date,...
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Benchmark history file does not exist: {file_path}"
        )

    rows: list[tuple[date, float]] = []

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.reader(file)

        raw_rows = list(reader)

    if len(raw_rows) < 4:
        raise ValueError(
            f"Benchmark history file has insufficient data: {file_path}"
        )

    header = raw_rows[0]

    try:
        adjusted_close_index = header.index("Adj Close")
    except ValueError as exc:
        raise ValueError(
            f"'Adj Close' column was not found in {file_path}"
        ) from exc

    for raw_row in raw_rows[3:]:
        if not raw_row:
            continue

        try:
            row_date = datetime.strptime(
                raw_row[0],
                "%Y-%m-%d",
            ).date()

            adjusted_close = float(
                raw_row[adjusted_close_index]
            )
        except (
            ValueError,
            TypeError,
            IndexError,
        ):
            continue

        rows.append(
            (
                row_date,
                adjusted_close,
            )
        )

    rows.sort(key=lambda item: item[0])

    return rows


def _simple_moving_average(
    values: list[float],
    period: int,
) -> float:
    """
    Calculate a simple moving average using the latest values.
    """
    if len(values) < period:
        raise ValueError(
            f"At least {period} values are required."
        )

    selected_values = values[-period:]

    return sum(selected_values) / period


def calculate_market_regime(
    measurement_date: Any,
    benchmark_file: str | Path | None = None,
) -> dict[str, Any]:
    """
    Classify the broad TSX market regime using XIC.

    IBKR regular traded daily history is primary when the
    default XIC benchmark is used.

    A supplied benchmark_file remains supported for tests
    and controlled historical research.

    Local saved benchmark history is retained as fallback.

    This classification may be consumed by research
    enrichment or by the Mean Reversion new-entry market guard.
    """

    result: dict[str, Any] = {
        "measurement_date": "",
        "benchmark": "XIC.TO",
        "regime": "",
        "benchmark_close": "",
        "sma_50": "",
        "sma_200": "",
        "close_vs_sma_200_percent": "",
        "sma_50_vs_sma_200_percent": "",
        "status": "UNAVAILABLE",
        "reason": "",
        "data_source": "UNAVAILABLE",
    }

    try:
        normalized_date = _normalize_date(
            measurement_date
        )

        result[
            "measurement_date"
        ] = normalized_date.isoformat()

        history = None
        ibkr_error = ""

        if benchmark_file is None:
            try:
                ibkr_history = (
                    load_ibkr_daily_history(
                        symbol="XIC.TO",
                        measurement_date=(
                            normalized_date.isoformat()
                        ),
                        duration="2 Y",
                        adjusted=False,
                        client_id=21,
                    )
                )

                if (
                    ibkr_history is not None
                    and len(ibkr_history) >= 200
                ):
                    history = [
                        (
                            row.date(),
                            float(close),
                        )
                        for row, close in zip(
                            ibkr_history["date"],
                            ibkr_history["close"],
                        )
                    ]

                    result[
                        "data_source"
                    ] = "IBKR_TRADES"

            except Exception as error:
                ibkr_error = str(
                    error
                )

                history = None

        if history is None:
            history_file = (
                Path(benchmark_file)
                if benchmark_file is not None
                else DEFAULT_BENCHMARK_FILE
            )

            history = _load_adjusted_closes(
                history_file
            )

            result[
                "data_source"
            ] = (
                "LOCAL_BENCHMARK_FILE"
                if benchmark_file is not None
                else "LOCAL_FALLBACK"
            )

        available_history = [
            item
            for item in history
            if item[0] <= normalized_date
        ]

        if len(available_history) < 200:
            result["reason"] = (
                "At least 200 benchmark trading "
                "days are required through "
                f"{normalized_date.isoformat()}; "
                f"only {len(available_history)} "
                "were available."
            )

            if ibkr_error:
                result["reason"] += (
                    " IBKR error: "
                    f"{ibkr_error}"
                )

            return result

        prices = [
            adjusted_close
            for _, adjusted_close
            in available_history
        ]

        benchmark_close = (
            prices[-1]
        )

        sma_50 = (
            _simple_moving_average(
                prices,
                50,
            )
        )

        sma_200 = (
            _simple_moving_average(
                prices,
                200,
            )
        )

        close_vs_sma_200_percent = (
            (
                benchmark_close
                / sma_200
            )
            - 1
        ) * 100

        sma_50_vs_sma_200_percent = (
            (
                sma_50
                / sma_200
            )
            - 1
        ) * 100

        if (
            benchmark_close > sma_200
            and sma_50 > sma_200
        ):
            regime = "BULL"

        elif (
            benchmark_close < sma_200
            and sma_50 < sma_200
        ):
            regime = "BEAR"

        else:
            regime = "SIDEWAYS"

        result.update(
            {
                "regime": regime,
                "benchmark_close": round(
                    benchmark_close,
                    4,
                ),
                "sma_50": round(
                    sma_50,
                    4,
                ),
                "sma_200": round(
                    sma_200,
                    4,
                ),
                "close_vs_sma_200_percent": round(
                    close_vs_sma_200_percent,
                    4,
                ),
                "sma_50_vs_sma_200_percent": round(
                    sma_50_vs_sma_200_percent,
                    4,
                ),
                "status": "AVAILABLE",
                "reason": "",
            }
        )

        return result

    except Exception as exc:
        result["reason"] = str(
            exc
        )

        return result
