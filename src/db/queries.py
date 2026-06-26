"""Read-only access to data/weather.db for the dashboard — Phase 4.

The dashboard reads ONLY from the local database (it never re-fetches). These are
pure pandas/sqlite functions with no Streamlit dependency, so they're unit-testable;
the app wraps load_daily() with st.cache_data. Phase 5 (Climate Insights) reuses them.
"""
from __future__ import annotations

import sqlite3

import pandas as pd

import config

# Canonical variable order for display (matches the seed in src/data/ingest.py).
VARIABLE_ORDER = [
    "max_temp", "min_temp", "mean_temp", "wet_bulb_temp", "relative_humidity",
    "precipitation", "wind_speed", "wind_direction", "station_pressure",
]


def load_daily(db_path=None, station_id: int = 1) -> pd.DataFrame:
    """Wide daily frame for one station: DatetimeIndex `date` × variable columns."""
    conn = sqlite3.connect(db_path or config.DB_PATH)
    try:
        long = pd.read_sql_query(
            "SELECT o.date, v.name, o.value "
            "FROM observation_daily o JOIN variable v ON o.variable_id = v.variable_id "
            "WHERE o.station_id = ? ORDER BY o.date",
            conn, params=(station_id,),
        )
    finally:
        conn.close()

    wide = long.pivot(index="date", columns="name", values="value")
    wide.index = pd.to_datetime(wide.index)
    wide.index.name = "date"
    wide.columns.name = None
    # Stable, meaningful column order; ignore any variable not present.
    cols = [c for c in VARIABLE_ORDER if c in wide.columns]
    return wide[cols].sort_index()


def variable_units(db_path=None) -> dict[str, str]:
    """Map variable name -> unit (for axis labels and metric suffixes)."""
    conn = sqlite3.connect(db_path or config.DB_PATH)
    try:
        rows = conn.execute("SELECT name, unit FROM variable").fetchall()
    finally:
        conn.close()
    return {name: unit for name, unit in rows}


def station_info(db_path=None, station_id: int = 1) -> dict:
    """Station metadata row as a dict (empty if not found)."""
    conn = sqlite3.connect(db_path or config.DB_PATH)
    try:
        row = conn.execute(
            "SELECT station_id, name, latitude, longitude, elevation, source "
            "FROM station WHERE station_id = ?",
            (station_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {}
    keys = ("station_id", "name", "latitude", "longitude", "elevation", "source")
    return dict(zip(keys, row))
