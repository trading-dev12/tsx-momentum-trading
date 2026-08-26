"""
Northstar Quant whole-strategy risk benchmark.

Creates a daily equity curve for a paper strategy and compares
it with a fully invested XIC.TO benchmark.

Northstar holdings:
    IBKR TRADES daily history.

XIC benchmark:
    IBKR ADJUSTED_LAST daily history.

This module is read-only research analytics.
It does not modify signals, portfolios, positions, journals,
pending trades, or strategy rules.
"""

from __future__ import annotations

from datetime import date, datetime
from math import sqrt
from statistics import stdev

from core.ibkr_data_provider import (
    IBKRDataProvider,
)
from core.market_hours import (
    get_tsx_market_status,
)
from research.ibkr_historical_research import (
    load_ibkr_daily_history,
)


BENCHMARK_SYMBOL = "XIC.TO"
RISK_IBKR_CLIENT_ID = 29


def _date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return datetime.strptime(
        str(value)[:10],
        "%Y-%m-%d",
    ).date()


def _entry_cost(trade):
    return (
        float(
            trade.get(
                "entry_price",
                0,
            )
            or 0
        )
        * int(
            trade.get(
                "shares",
                0,
            )
            or 0
        )
    )


def _exit_proceeds(trade):
    return (
        float(
            trade.get(
                "exit_price",
                0,
            )
            or 0
        )
        * int(
            trade.get(
                "shares",
                0,
            )
            or 0
        )
    )


def _frame_history(frame):
    history = []

    for _, row in frame.iterrows():
        history.append(
            {
                "date": _date(
                    row["date"]
                ),
                "close": float(
                    row["close"]
                ),
            }
        )

    history.sort(
        key=lambda row: row["date"]
    )

    return history


def _price_on_or_before(
    history,
    target_date,
):
    target_date = _date(
        target_date
    )

    eligible = [
        row
        for row in history
        if row["date"] <= target_date
    ]

    if not eligible:
        raise ValueError(
            "No historical price available "
            f"through {target_date}."
        )

    return float(
        eligible[-1]["close"]
    )


def _max_drawdown(
    values,
):
    if not values:
        return 0.0

    peak = float(
        values[0]
    )

    worst = 0.0

    for value in values:
        value = float(value)

        if value > peak:
            peak = value

        if peak <= 0:
            continue

        drawdown = (
            value / peak
            - 1
        )

        worst = min(
            worst,
            drawdown,
        )

    return worst * 100


def _annualized_volatility(
    values,
):
    if len(values) < 3:
        return 0.0

    returns = []

    for previous, current in zip(
        values,
        values[1:],
    ):
        previous = float(
            previous
        )

        current = float(
            current
        )

        if previous <= 0:
            continue

        returns.append(
            current / previous
            - 1
        )

    if len(returns) < 2:
        return 0.0

    return (
        stdev(returns)
        * sqrt(252)
        * 100
    )


def _calculate_required_capital(
    trades,
    calendar,
):
    """
    Minimum starting cash required to execute the observed
    trade sequence without borrowing.

    Entries are conservatively processed before exits on a
    given day. This prevents us from assuming that end-of-day
    exit proceeds were available for morning entries.
    """

    cash_flow = 0.0
    minimum_cash_flow = 0.0

    for trading_day in calendar:
        entries = [
            trade
            for trade in trades
            if (
                trade.get("entry_date")
                and _date(
                    trade["entry_date"]
                ) == trading_day
            )
        ]

        exits = [
            trade
            for trade in trades
            if (
                trade.get("exit_date")
                and _date(
                    trade["exit_date"]
                ) == trading_day
            )
        ]

        for trade in entries:
            cash_flow -= (
                _entry_cost(
                    trade
                )
            )

        minimum_cash_flow = min(
            minimum_cash_flow,
            cash_flow,
        )

        for trade in exits:
            cash_flow += (
                _exit_proceeds(
                    trade
                )
            )

    return max(
        0.0,
        -minimum_cash_flow,
    )


def calculate_whole_strategy_metrics(
    open_positions,
    closed_trades,
    stock_histories,
    xic_history,
    risk_end_date=None,
):
    """
    Pure calculation layer.

    stock_histories:
        {
            "ABC.TO": [
                {"date": date(...), "close": 123.45},
                ...
            ]
        }

    xic_history:
        adjusted XIC closes in the same structure.
    """

    open_positions = list(
        open_positions
    )

    closed_trades = list(
        closed_trades
    )

    all_trades = (
        closed_trades
        + open_positions
    )

    if not all_trades:
        return {
            "status": "AVAILABLE",
            "required_starting_capital": 0.0,
            "peak_capital_deployed": 0.0,
            "strategy_return": 0.0,
            "xic_return": 0.0,
            "excess_return": 0.0,
            "strategy_max_drawdown": 0.0,
            "xic_max_drawdown": 0.0,
            "strategy_volatility": 0.0,
            "xic_volatility": 0.0,
            "average_capital_deployed": 0.0,
            "average_capital_utilization": 0.0,
            "time_in_market": 0.0,
            "risk_through": "--",
            "trading_since": "--",
            "days_measured": 0,
        }

    entry_dates = [
        _date(
            trade["entry_date"]
        )
        for trade in all_trades
        if trade.get(
            "entry_date"
        )
    ]

    if not entry_dates:
        raise ValueError(
            "Trades contain no entry dates."
        )

    first_date = min(
        entry_dates
    )

    if not xic_history:
        raise ValueError(
            "XIC history is empty."
        )

    if risk_end_date is None:
        risk_end_date = (
            xic_history[-1]["date"]
        )
    else:
        risk_end_date = _date(
            risk_end_date
        )

    calendar = [
        row["date"]
        for row in xic_history
        if (
            first_date
            <= row["date"]
            <= risk_end_date
        )
    ]

    if not calendar:
        raise ValueError(
            "No benchmark trading dates overlap "
            "the strategy period."
        )

    calendar_set = set(
        calendar
    )

    #
    # Every historical trade date should be an actual
    # XIC/TSX trading day. Fail rather than silently shift
    # dates and distort the comparison.
    #
    for trade in all_trades:
        entry_date = trade.get(
            "entry_date"
        )

        if entry_date:
            normalized = _date(
                entry_date
            )

            if (
                normalized <= risk_end_date
                and normalized
                not in calendar_set
            ):
                raise ValueError(
                    "Entry date is not present in "
                    "the XIC trading calendar: "
                    f"{normalized}"
                )

        exit_date = trade.get(
            "exit_date"
        )

        if exit_date:
            normalized = _date(
                exit_date
            )

            if (
                normalized <= risk_end_date
                and normalized
                not in calendar_set
            ):
                raise ValueError(
                    "Exit date is not present in "
                    "the XIC trading calendar: "
                    f"{normalized}"
                )

    required_capital = (
        _calculate_required_capital(
            all_trades,
            calendar,
        )
    )

    if required_capital <= 0:
        raise ValueError(
            "Required starting capital could not "
            "be calculated."
        )

    cash = required_capital

    strategy_equity = []
    xic_equity = []

    deployed_capital_series = []

    first_xic_price = (
        _price_on_or_before(
            xic_history,
            calendar[0],
        )
    )

    peak_capital_deployed = 0.0

    days_with_exposure = 0

    for trading_day in calendar:

        #
        # Morning / entry-side cash usage.
        #
        entering = [
            trade
            for trade in all_trades
            if (
                trade.get("entry_date")
                and _date(
                    trade["entry_date"]
                ) == trading_day
            )
        ]

        for trade in entering:
            cash -= (
                _entry_cost(
                    trade
                )
            )

        #
        # Positions active before end-of-day exits.
        # Used for capital deployment statistics.
        #
        active_before_exit = []

        for trade in all_trades:
            if not trade.get(
                "entry_date"
            ):
                continue

            entry_date = _date(
                trade["entry_date"]
            )

            exit_date = (
                _date(
                    trade["exit_date"]
                )
                if trade.get(
                    "exit_date"
                )
                else None
            )

            if entry_date > trading_day:
                continue

            if (
                exit_date is not None
                and exit_date
                < trading_day
            ):
                continue

            active_before_exit.append(
                trade
            )

        deployed_capital = sum(
            _entry_cost(
                trade
            )
            for trade
            in active_before_exit
        )

        deployed_capital_series.append(
            deployed_capital
        )

        peak_capital_deployed = max(
            peak_capital_deployed,
            deployed_capital,
        )

        if deployed_capital > 0:
            days_with_exposure += 1

        #
        # End-of-day exits use the actual paper exit price.
        #
        exiting = [
            trade
            for trade in closed_trades
            if (
                trade.get("exit_date")
                and _date(
                    trade["exit_date"]
                ) == trading_day
            )
        ]

        for trade in exiting:
            cash += (
                _exit_proceeds(
                    trade
                )
            )

        #
        # Positions remaining open after today's exits
        # are marked to the IBKR daily traded close.
        #
        remaining_positions = []

        for trade in all_trades:
            if not trade.get(
                "entry_date"
            ):
                continue

            entry_date = _date(
                trade["entry_date"]
            )

            exit_date = (
                _date(
                    trade["exit_date"]
                )
                if trade.get(
                    "exit_date"
                )
                else None
            )

            if entry_date > trading_day:
                continue

            if (
                exit_date is not None
                and exit_date
                <= trading_day
            ):
                continue

            remaining_positions.append(
                trade
            )

        market_value = 0.0

        for trade in remaining_positions:
            symbol = str(
                trade.get(
                    "symbol",
                    "",
                )
            )

            history = (
                stock_histories.get(
                    symbol
                )
            )

            if not history:
                raise ValueError(
                    "Missing IBKR history for "
                    f"{symbol}."
                )

            price = (
                _price_on_or_before(
                    history,
                    trading_day,
                )
            )

            shares = int(
                trade.get(
                    "shares",
                    0,
                )
                or 0
            )

            market_value += (
                price * shares
            )

        equity = (
            cash
            + market_value
        )

        strategy_equity.append(
            equity
        )

        xic_price = (
            _price_on_or_before(
                xic_history,
                trading_day,
            )
        )

        xic_equity.append(
            required_capital
            * (
                xic_price
                / first_xic_price
            )
        )

    final_strategy_equity = (
        strategy_equity[-1]
    )

    final_xic_equity = (
        xic_equity[-1]
    )

    strategy_return = (
        (
            final_strategy_equity
            / required_capital
        )
        - 1
    ) * 100

    xic_return = (
        (
            final_xic_equity
            / required_capital
        )
        - 1
    ) * 100

    average_deployed = (
        sum(
            deployed_capital_series
        )
        / len(
            deployed_capital_series
        )
    )

    average_utilization = (
        (
            average_deployed
            / required_capital
        )
        * 100
        if required_capital > 0
        else 0.0
    )

    time_in_market = (
        (
            days_with_exposure
            / len(calendar)
        )
        * 100
        if calendar
        else 0.0
    )

    return {
        "status": "AVAILABLE",
        "benchmark": BENCHMARK_SYMBOL,
        "required_starting_capital": (
            required_capital
        ),
        "peak_capital_deployed": (
            peak_capital_deployed
        ),
        "ending_strategy_equity": (
            final_strategy_equity
        ),
        "ending_xic_equity": (
            final_xic_equity
        ),
        "strategy_return": (
            strategy_return
        ),
        "xic_return": (
            xic_return
        ),
        "excess_return": (
            strategy_return
            - xic_return
        ),
        "dollar_advantage": (
            final_strategy_equity
            - final_xic_equity
        ),
        "strategy_max_drawdown": (
            _max_drawdown(
                strategy_equity
            )
        ),
        "xic_max_drawdown": (
            _max_drawdown(
                xic_equity
            )
        ),
        "strategy_volatility": (
            _annualized_volatility(
                strategy_equity
            )
        ),
        "xic_volatility": (
            _annualized_volatility(
                xic_equity
            )
        ),
        "average_capital_deployed": (
            average_deployed
        ),
        "average_capital_utilization": (
            average_utilization
        ),
        "time_in_market": (
            time_in_market
        ),
        "trading_since": (
            calendar[0].isoformat()
        ),
        "risk_through": (
            calendar[-1].isoformat()
        ),
        "days_measured": len(
            calendar
        ),
        "strategy_equity_curve": [
            {
                "date": day.isoformat(),
                "equity": equity,
            }
            for day, equity
            in zip(
                calendar,
                strategy_equity,
            )
        ],
        "xic_equity_curve": [
            {
                "date": day.isoformat(),
                "equity": equity,
            }
            for day, equity
            in zip(
                calendar,
                xic_equity,
            )
        ],
    }


def build_whole_strategy_metrics(
    open_positions,
    closed_trades,
):
    """
    Production IBKR loader + calculation.
    """

    all_trades = (
        list(closed_trades)
        + list(open_positions)
    )

    if not all_trades:
        return (
            calculate_whole_strategy_metrics(
                [],
                [],
                {},
                [],
            )
        )

    entry_dates = [
        _date(
            trade["entry_date"]
        )
        for trade in all_trades
        if trade.get(
            "entry_date"
        )
    ]

    if not entry_dates:
        return {
            "status": "UNAVAILABLE",
            "reason": (
                "No strategy entry dates."
            ),
        }

    first_date = min(
        entry_dates
    )

    provider = IBKRDataProvider(
        client_id=RISK_IBKR_CLIENT_ID
    )

    try:
        xic_frame = (
            load_ibkr_daily_history(
                symbol=BENCHMARK_SYMBOL,
                measurement_date=None,
                duration="1 Y",
                adjusted=True,
                provider=provider,
            )
        )

        xic_history = (
            _frame_history(
                xic_frame
            )
        )

        xic_history = [
            row
            for row in xic_history
            if row["date"]
            >= first_date
        ]

        if not xic_history:
            raise ValueError(
                "IBKR returned no XIC history "
                "for strategy period."
            )

        market_status = (
            get_tsx_market_status()
        )

        #
        # Do not use an unfinished current-day daily bar
        # for volatility/drawdown calculations.
        #
        if (
            market_status.get(
                "is_open"
            )
            and len(
                xic_history
            ) >= 2
            and xic_history[-1]["date"]
            == datetime.now().date()
        ):
            xic_history = (
                xic_history[:-1]
            )

        risk_end_date = (
            xic_history[-1]["date"]
        )

        symbols = sorted(
            {
                str(
                    trade.get(
                        "symbol",
                        "",
                    )
                )
                for trade in all_trades
                if trade.get(
                    "symbol"
                )
                and _date(
                    trade[
                        "entry_date"
                    ]
                )
                <= risk_end_date
            }
        )

        stock_histories = {}

        for symbol in symbols:
            frame = (
                load_ibkr_daily_history(
                    symbol=symbol,
                    measurement_date=(
                        risk_end_date
                    ),
                    duration="1 Y",
                    adjusted=False,
                    provider=provider,
                )
            )

            history = (
                _frame_history(
                    frame
                )
            )

            if not history:
                raise ValueError(
                    "IBKR returned no traded "
                    f"history for {symbol}."
                )

            stock_histories[
                symbol
            ] = history

            #
            # Gentle spacing between historical requests.
            #
            provider.ib.sleep(
                0.15
            )

        result = (
            calculate_whole_strategy_metrics(
                open_positions,
                closed_trades,
                stock_histories,
                xic_history,
                risk_end_date=(
                    risk_end_date
                ),
            )
        )

        result[
            "strategy_price_source"
        ] = "IBKR_TRADES"

        result[
            "benchmark_price_source"
        ] = "IBKR_ADJUSTED_LAST"

        return result

    except Exception as error:
        return {
            "status": "UNAVAILABLE",
            "benchmark": (
                BENCHMARK_SYMBOL
            ),
            "reason": str(
                error
            ),
        }

    finally:
        provider.disconnect()
