"""Phase 4 unit tests for the read-only DB layer (src/db/queries.py).

Builds a tiny database from the real schema.sql in a temp dir, so the tests are
deterministic and never touch the local data/weather.db.

Run with:  pytest
"""
import sqlite3

import pandas as pd

import config
from src.db import queries

SCHEMA = (config.PROJECT_ROOT / "src" / "db" / "schema.sql").read_text()


def _make_db(path):
    """Two stations, two variables, two dates of observations for station 1."""
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO station VALUES (1, 'Open-Meteo @ UPLB', 14.17, 121.24, NULL, 'open-meteo')")
    conn.execute("INSERT INTO station VALUES (2, 'Other', 0.0, 0.0, NULL, 'x')")
    conn.executemany("INSERT INTO variable VALUES (?, ?, ?, ?)", [
        (1, "max_temp", "°C", "daily max"),
        (2, "min_temp", "°C", "daily min"),
    ])
    conn.executemany("INSERT INTO observation_daily VALUES (?, ?, ?, ?)", [
        (1, "2020-01-01", 1, 32.0), (1, "2020-01-01", 2, 24.0),
        (1, "2020-01-02", 1, 33.0), (1, "2020-01-02", 2, 25.0),
        (2, "2020-01-01", 1, 99.0), (2, "2020-01-01", 2, 88.0),  # other station
    ])
    conn.commit()
    conn.close()


def test_load_daily_wide_shape_and_index(tmp_path):
    db = tmp_path / "weather.db"
    _make_db(db)
    df = queries.load_daily(db_path=db, station_id=1)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert set(df.columns) == {"max_temp", "min_temp"}
    assert len(df) == 2
    assert df.loc["2020-01-02", "max_temp"] == 33.0
    # Column order follows VARIABLE_ORDER (max before min).
    assert list(df.columns) == ["max_temp", "min_temp"]


def test_load_daily_filters_by_station(tmp_path):
    db = tmp_path / "weather.db"
    _make_db(db)
    df = queries.load_daily(db_path=db, station_id=1)
    # Station 2's value (99.0) must not leak in.
    assert 99.0 not in df["max_temp"].values
    other = queries.load_daily(db_path=db, station_id=2)
    assert other.loc["2020-01-01", "max_temp"] == 99.0


def test_variable_units(tmp_path):
    db = tmp_path / "weather.db"
    _make_db(db)
    assert queries.variable_units(db_path=db) == {"max_temp": "°C", "min_temp": "°C"}


def test_station_info(tmp_path):
    db = tmp_path / "weather.db"
    _make_db(db)
    info = queries.station_info(db_path=db, station_id=1)
    assert info["name"] == "Open-Meteo @ UPLB"
    assert info["source"] == "open-meteo"
    assert queries.station_info(db_path=db, station_id=99) == {}
