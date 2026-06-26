"""Read-only data access for the Dash app — reuses the framework-agnostic layer.

The SQLite database is static, so each query is loaded once and cached. The
underlying logic lives in src/db/queries.py (shared with the old Streamlit app).
"""
from functools import lru_cache

import pandas as pd

from src.db import queries
from src.features import heat_index


@lru_cache(maxsize=1)
def daily():
    """Wide daily frame: DatetimeIndex × the 9 canonical variables."""
    return queries.load_daily()


@lru_cache(maxsize=1)
def units():
    """{variable name: unit}."""
    return queries.variable_units()


@lru_cache(maxsize=1)
def station():
    """Station metadata dict."""
    return queries.station_info()


@lru_cache(maxsize=1)
def heat_index_daily() -> pd.DataFrame:
    """Daily heat index (°C) + PAGASA band, from daily Tmax + mean RH.

    NOTE: pairing daily max temperature with daily *mean* relative humidity tends
    to OVERESTIMATE the heat index (humidity is lowest at peak heat). Reused by
    Climate Insights (Phase 5) and the forecast (Phase 6).
    """
    df = daily()
    if df.empty:
        return pd.DataFrame(columns=["hi_c", "band"])
    hi = heat_index.heat_index_c(df["max_temp"].to_numpy(), df["relative_humidity"].to_numpy())
    out = pd.DataFrame({"hi_c": hi}, index=df.index)
    out["band"] = heat_index.classify(out["hi_c"].to_numpy())
    return out


def clear():
    """Drop the caches (used by tests that swap the database)."""
    daily.cache_clear()
    units.cache_clear()
    station.cache_clear()
    heat_index_daily.cache_clear()
