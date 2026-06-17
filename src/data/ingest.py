"""Ingestion pipeline: raw -> clean -> SQLite (data/weather.db) — Phase 2.

Builds the relational database from src/db/schema.sql, seeds the station and
variable tables, and loads the cleaned daily record into observation_daily
(long format). Idempotent: each run rebuilds the database from scratch.

Run with:  python -m src.data.ingest
"""
from __future__ import annotations

import sqlite3

import pandas as pd

import config
from src.data.clean import clean

SCHEMA_PATH = config.PROJECT_ROOT / "src" / "db" / "schema.sql"

# The one stand-in station for now; the UPLB-NAS row is added in Phase 8.
STATION = (1, "Open-Meteo ERA5 @ UPLB", config.LAT, config.LON, None, "open-meteo")

# Canonical variables (variable_id, name, unit, description). Order/ids are stable.
VARIABLES = [
    (1, "max_temp", "°C", "Daily maximum air (dry-bulb) temperature"),
    (2, "min_temp", "°C", "Daily minimum air (dry-bulb) temperature"),
    (3, "mean_temp", "°C", "Daily mean air (dry-bulb) temperature"),
    (4, "wet_bulb_temp", "°C", "Daily mean wet-bulb temperature"),
    (5, "relative_humidity", "%", "Daily mean relative humidity"),
    (6, "precipitation", "mm", "Daily total precipitation (rainfall)"),
    (7, "wind_speed", "m/s", "Daily mean wind speed at 10 m"),
    (8, "wind_direction", "°", "Dominant daily wind direction at 10 m"),
    (9, "station_pressure", "hPa", "Daily mean surface (station) pressure"),
]
_NAME_TO_ID = {name: vid for vid, name, _unit, _desc in VARIABLES}


def _to_long(daily: pd.DataFrame) -> list[tuple]:
    """Melt the wide daily frame to (station_id, date, variable_id, value) rows."""
    long = daily.melt(id_vars="date", var_name="name", value_name="value")
    dates = pd.to_datetime(long["date"]).dt.strftime("%Y-%m-%d")
    return [
        (STATION[0], d, int(_NAME_TO_ID[n]), (None if pd.isna(v) else float(v)))
        for d, n, v in zip(dates, long["name"], long["value"])
    ]


def _summary(conn: sqlite3.Connection) -> None:
    n_station = conn.execute("SELECT COUNT(*) FROM station").fetchone()[0]
    n_var = conn.execute("SELECT COUNT(*) FROM variable").fetchone()[0]
    n_obs = conn.execute("SELECT COUNT(*) FROM observation_daily").fetchone()[0]
    d0, d1, n_dates = conn.execute(
        "SELECT MIN(date), MAX(date), COUNT(DISTINCT date) FROM observation_daily"
    ).fetchone()
    print(f"Built {config.DB_PATH}")
    print(f"  stations: {n_station} | variables: {n_var} | observations: {n_obs:,}")
    print(f"  dates: {n_dates:,} ({d0} → {d1})")


def build_db() -> None:
    """Rebuild data/weather.db from the cleaned raw data."""
    daily = clean()

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    if config.DB_PATH.exists():
        config.DB_PATH.unlink()

    conn = sqlite3.connect(config.DB_PATH)
    try:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("INSERT INTO station VALUES (?, ?, ?, ?, ?, ?)", STATION)
        conn.executemany("INSERT INTO variable VALUES (?, ?, ?, ?)", VARIABLES)
        conn.executemany(
            "INSERT INTO observation_daily VALUES (?, ?, ?, ?)", _to_long(daily)
        )
        conn.commit()
        _summary(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    build_db()
