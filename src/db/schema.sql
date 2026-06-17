-- Relational schema for the weather database (data/weather.db) — Phase 2.

CREATE TABLE station (
    station_id  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    latitude    REAL NOT NULL,
    longitude   REAL NOT NULL,
    elevation   REAL,
    source      TEXT NOT NULL              -- 'open-meteo' | 'uplb-nas'
);

CREATE TABLE variable (
    variable_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,      -- 'max_temp', 'relative_humidity', ...
    unit        TEXT NOT NULL,             -- '°C', '%', 'mm', 'm/s', '°', 'hPa'
    description TEXT
);

CREATE TABLE observation_daily (
    station_id  INTEGER NOT NULL REFERENCES station(station_id),
    date        TEXT    NOT NULL,          -- ISO 'YYYY-MM-DD'
    variable_id INTEGER NOT NULL REFERENCES variable(variable_id),
    value       REAL,                      -- nullable: real station has gaps
    PRIMARY KEY (station_id, date, variable_id)
);

-- Time-series queries hit one variable across a date range.
CREATE INDEX idx_obs_var_date ON observation_daily(variable_id, date);
