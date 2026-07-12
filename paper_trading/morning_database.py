"""
Morning Market Database

Stores timestamped intraday observations for pending paper-trade
candidates.

This database is for research only. It does not make trading
decisions and does not alter the baseline paper-execution engine.
"""

import os
import sqlite3


RUNTIME_DATA_FOLDER = os.path.join(
    "data",
    "runtime",
)

DEFAULT_DATABASE_FILE = os.path.join(
    RUNTIME_DATA_FOLDER,
    "morning_market_data.db",
)


CREATE_OBSERVATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS intraday_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_date TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    observation_time TEXT NOT NULL,
    observation_timestamp TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    cumulative_volume INTEGER,
    previous_close REAL,
    previous_high REAL,
    gap_percent REAL,
    distance_from_open_percent REAL,
    distance_from_previous_high_percent REAL,
    atr REAL,
    tmqs REAL,
    rvol REAL,
    breakout TEXT,
    baseline_entry_price REAL,
    data_source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (
        symbol,
        observation_timestamp
    )
)
"""


CREATE_SYMBOL_INDEX = """
CREATE INDEX IF NOT EXISTS
idx_intraday_observations_symbol_date
ON intraday_observations (
    symbol,
    observation_date
)
"""


def ensure_database_folder(database_file):
    """
    Create the database's parent folder when necessary.
    """

    folder = os.path.dirname(
        os.path.abspath(database_file)
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )


def get_connection(
    database_file=DEFAULT_DATABASE_FILE,
):
    """
    Open a SQLite connection with named-column access.
    """

    ensure_database_folder(
        database_file
    )

    connection = sqlite3.connect(
        database_file
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database(
    database_file=DEFAULT_DATABASE_FILE,
):
    """
    Create the morning-observation database structure.
    """

    with get_connection(database_file) as connection:
        connection.execute(
            CREATE_OBSERVATIONS_TABLE
        )

        connection.execute(
            CREATE_SYMBOL_INDEX
        )

        connection.commit()

    return {
        "success": True,
        "database_file": database_file,
        "message": (
            "Morning market database initialized."
        ),
    }


def save_observation(
    observation,
    database_file=DEFAULT_DATABASE_FILE,
):
    """
    Save one timestamped intraday observation.

    Duplicate symbol/timestamp observations are ignored so the
    recorder can retry safely without creating duplicate rows.
    """

    required_fields = [
        "symbol",
        "signal_date",
        "observation_date",
        "observation_time",
        "observation_timestamp",
        "data_source",
    ]

    missing_fields = [
        field
        for field in required_fields
        if not observation.get(field)
    ]

    if missing_fields:
        return {
            "success": False,
            "inserted": False,
            "message": (
                "Missing required observation fields: "
                + ", ".join(missing_fields)
            ),
        }

    initialize_database(
        database_file=database_file
    )

    fields = [
        "symbol",
        "signal_date",
        "observation_date",
        "observation_time",
        "observation_timestamp",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "cumulative_volume",
        "previous_close",
        "previous_high",
        "gap_percent",
        "distance_from_open_percent",
        "distance_from_previous_high_percent",
        "atr",
        "tmqs",
        "rvol",
        "breakout",
        "baseline_entry_price",
        "data_source",
    ]

    values = [
        observation.get(field)
        for field in fields
    ]

    placeholders = ", ".join(
        "?"
        for _ in fields
    )

    field_list = ", ".join(fields)

    insert_sql = (
        "INSERT OR IGNORE INTO "
        "intraday_observations "
        f"({field_list}) "
        f"VALUES ({placeholders})"
    )

    with get_connection(database_file) as connection:
        cursor = connection.execute(
            insert_sql,
            values,
        )

        connection.commit()

        inserted = cursor.rowcount == 1

    return {
        "success": True,
        "inserted": inserted,
        "message": (
            "Observation saved."
            if inserted
            else "Duplicate observation ignored."
        ),
    }


def get_observations(
    symbol=None,
    observation_date=None,
    database_file=DEFAULT_DATABASE_FILE,
):
    """
    Return saved observations in chronological order.
    """

    initialize_database(
        database_file=database_file
    )

    query = """
        SELECT *
        FROM intraday_observations
        WHERE 1 = 1
    """

    parameters = []

    if symbol is not None:
        query += " AND symbol = ?"
        parameters.append(symbol)

    if observation_date is not None:
        query += " AND observation_date = ?"
        parameters.append(observation_date)

    query += """
        ORDER BY observation_timestamp ASC
    """

    with get_connection(database_file) as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]