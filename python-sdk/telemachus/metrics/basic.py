from __future__ import annotations

import numpy as np
import pandas as pd


def compute_dt(ts: pd.Series) -> pd.Series:
    """
    Delta t in seconds (NaN for first row).
    """
    ts = pd.to_datetime(ts, utc=True, errors="coerce")
    return ts.diff().dt.total_seconds()


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    """
    Elementwise haversine distance in meters between (lat1, lon1) and (lat2, lon2).
    """
    R = 6_371_000.0
    lat1 = np.radians(lat1); lon1 = np.radians(lon1)
    lat2 = np.radians(lat2); lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c


def speed_from_pos(df: pd.DataFrame) -> pd.Series:
    """
    Estimate speed (m/s) from timestamp+lat/lon (forward difference).
    Returns a Series aligned with df.index (first row NaN).
    """
    dt = compute_dt(df["timestamp"]).to_numpy()
    dist = haversine_m(
        df["lat"].shift(1).to_numpy(), df["lon"].shift(1).to_numpy(),
        df["lat"].to_numpy(),          df["lon"].to_numpy()
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        v = dist / dt
    if len(v):
        v[0] = np.nan
    return pd.Series(v, index=df.index, name="speed_from_pos")