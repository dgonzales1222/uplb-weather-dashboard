"""Short-term heat-index forecast — LSTM (PyTorch) — Phase 6.

A univariate LSTM with day-of-year seasonality features forecasts the daily heat
index; MAE / RMSE come from a holdout backtest. Pure functions (no Dash); the app
caches and renders them.

PyTorch is used rather than TensorFlow: TF/Keras `model.fit` deadlocked at 0% CPU
on macOS arm64 for real-data sizes. PyTorch runs eagerly and trains reliably.

Public API (unchanged, so the data layer + page are untouched):
    fit_forecast(series, horizon)  -> DataFrame[ds, yhat, yhat_lower, yhat_upper]
    backtest(series, horizon)      -> {"mae": float, "rmse": float}
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Hyperparameters — module-level so tests can shrink them for speed. Kept modest:
# a 2-week daily forecast needs neither a long lookback nor 30 years of history.
LOOKBACK = 45
EPOCHS = 40
UNITS = 48
SEED = 42
MAX_TRAIN_DAYS = 365 * 10  # recent ~10 years (tuned via rolling backtest: a longer
                           # lookback + larger net + more history cut 14-day MAE ~19%)
_BATCH = 32
_LR = 0.01


def _doy_features(dates) -> np.ndarray:
    """sin/cos of day-of-year -> (n, 2); known for future days too."""
    doy = pd.DatetimeIndex(dates).dayofyear.to_numpy()
    ang = 2 * np.pi * doy / 365.0
    return np.column_stack([np.sin(ang), np.cos(ang)])


def _scale(values, vmin, vmax):
    return (values - vmin) / (vmax - vmin) if vmax > vmin else np.zeros_like(values)


def _windows(feats: np.ndarray, target: np.ndarray):
    """feats (n,3), target (n,) -> X (m, LOOKBACK, 3), y (m,) as float32."""
    X = np.array([feats[i - LOOKBACK:i] for i in range(LOOKBACK, len(feats))], dtype="float32")
    return X, target[LOOKBACK:].astype("float32")


def _device():
    """Apple-Silicon GPU (MPS) when available, else CPU — keeps deploy portable."""
    import torch
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def _make_model(units):
    import torch.nn as nn

    class _LSTMNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(input_size=3, hidden_size=units, batch_first=True)
            self.fc = nn.Linear(units, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :]).squeeze(-1)

    return _LSTMNet()


def _train(series: pd.Series):
    """Train an LSTM on the recent window; return (model, vmin, vmax, resid_std)."""
    import torch
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = _device()

    s = series.dropna().iloc[-MAX_TRAIN_DAYS:]
    vals = s.to_numpy(dtype=float)
    vmin, vmax = float(vals.min()), float(vals.max())
    scaled = _scale(vals, vmin, vmax)
    feats = np.column_stack([scaled, _doy_features(s.index)]).astype("float32")
    X, y = _windows(feats, scaled)
    Xt, yt = torch.from_numpy(X).to(device), torch.from_numpy(y).to(device)

    model = _make_model(UNITS).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=_LR)
    loss_fn = torch.nn.MSELoss()

    n = len(Xt)
    best, patience = float("inf"), 0
    model.train()
    for _ in range(EPOCHS):
        perm = torch.randperm(n, device=device)
        total = 0.0
        for i in range(0, n, _BATCH):
            b = perm[i:i + _BATCH]
            opt.zero_grad()
            loss = loss_fn(model(Xt[b]), yt[b])
            loss.backward()
            opt.step()
            total += loss.item() * len(b)
        epoch_loss = total / max(n, 1)
        if epoch_loss < best - 1e-4:
            best, patience = epoch_loss, 0
        else:
            patience += 1
            if patience >= 3:   # early stop on training loss
                break

    model.eval()
    with torch.no_grad():
        resid = (yt.cpu().numpy() - model(Xt).cpu().numpy()) * (vmax - vmin)
    return model, vmin, vmax, float(np.std(resid))


def _recursive_forecast(model, series: pd.Series, vmin, vmax, horizon: int):
    """Recursively predict `horizon` days; return (future_dates, yhat in °C)."""
    import torch
    s = series.dropna()
    feats = np.column_stack([_scale(s.to_numpy(dtype=float), vmin, vmax),
                             _doy_features(s.index)]).astype("float32")
    window = feats[-LOOKBACK:].copy()
    future_dates = pd.date_range(pd.Timestamp(s.index[-1]) + pd.Timedelta(days=1),
                                 periods=horizon, freq="D")
    future_doy = _doy_features(future_dates).astype("float32")

    device = next(model.parameters()).device
    preds = []
    model.eval()
    with torch.no_grad():
        for k in range(horizon):
            x = torch.from_numpy(window.reshape(1, LOOKBACK, 3)).to(device)
            preds.append(float(model(x).item()))
            window = np.vstack(
                [window[1:], [preds[-1], future_doy[k, 0], future_doy[k, 1]]]
            ).astype("float32")
    return future_dates, np.array(preds) * (vmax - vmin) + vmin


def fit_forecast(series: pd.Series, horizon: int = 14) -> pd.DataFrame:
    """Train on the recent series; return the next `horizon` days of forecast."""
    model, vmin, vmax, resid_std = _train(series)
    dates, yhat = _recursive_forecast(model, series, vmin, vmax, horizon)
    band = 1.96 * resid_std
    return pd.DataFrame({"ds": dates, "yhat": yhat,
                         "yhat_lower": yhat - band, "yhat_upper": yhat + band})


def backtest(series: pd.Series, horizon: int = 14) -> dict:
    """Hold out the last `horizon` days, train on the rest, return MAE/RMSE (°C)."""
    s = series.dropna()
    train, actual = s.iloc[:-horizon], s.iloc[-horizon:].to_numpy(dtype=float)
    model, vmin, vmax, _ = _train(train)
    _, yhat = _recursive_forecast(model, train, vmin, vmax, horizon)
    err = actual - yhat
    return {"mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2)))}
