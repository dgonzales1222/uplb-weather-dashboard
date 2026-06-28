"""Phase 6 tests for the LSTM forecast (src/models/forecast.py).

Uses a small synthetic seasonal series with a tiny LSTM config (few epochs, short
lookback) so training stays fast. Run with:  pytest
"""
import numpy as np
import pandas as pd
import pytest

from src.models import forecast


@pytest.fixture(autouse=True)
def _tiny_lstm(monkeypatch):
    """Shrink the network so tests train in a couple of seconds."""
    monkeypatch.setattr(forecast, "EPOCHS", 2)
    monkeypatch.setattr(forecast, "LOOKBACK", 10)
    monkeypatch.setattr(forecast, "UNITS", 8)


def _series(n: int = 400) -> pd.Series:
    """Daily values: seasonal cycle around 30 °C + light noise."""
    idx = pd.date_range("2019-01-01", periods=n, freq="D")
    doy = idx.dayofyear.to_numpy()
    y = 30 + 5 * np.sin(2 * np.pi * doy / 365) + np.random.default_rng(0).normal(0, 0.5, n)
    return pd.Series(y, index=idx)


def test_fit_forecast_shape():
    fc = forecast.fit_forecast(_series(), horizon=14)
    assert len(fc) == 14
    assert list(fc.columns) == ["ds", "yhat", "yhat_lower", "yhat_upper"]
    assert (fc["yhat_upper"] >= fc["yhat_lower"]).all()
    # forecast dates are strictly after the last observed date
    assert fc["ds"].iloc[0] > _series().index[-1]


def test_backtest_metrics_finite_and_nonnegative():
    m = forecast.backtest(_series(), horizon=14)
    assert set(m) == {"mae", "rmse"}
    assert m["mae"] >= 0 and m["rmse"] >= 0
    assert np.isfinite(m["mae"]) and np.isfinite(m["rmse"])
    assert m["rmse"] >= m["mae"] - 1e-9  # RMSE >= MAE
