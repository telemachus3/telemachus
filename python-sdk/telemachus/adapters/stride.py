"""
STRIDE adapter — Figshare 25460755 (Rajshahi, Bangladesh).

POCO X2 Android smartphone: 100 Hz accel+gyro+magneto, 1 Hz GPS.
All raw units already in SI (m/s², rad/s, µT, m/s, degrees).
Uses TotalAcceleration.csv (raw with gravity), not Accelerometer.csv.

Reference: Naznine et al. (2024), Nature Scientific Data, CC-BY-4.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def load(
    source_path: str | Path,
    *,
    category: str = "driving",
    session_idx: Optional[int] = None,
    with_gyro: bool = True,
    with_magneto: bool = True,
) -> pd.DataFrame:
    """Load STRIDE dataset and return a Telemachus-conformant DataFrame.

    Parameters
    ----------
    source_path : str or Path
        Directory containing "Driving Behaviour" and/or "Road Anomalies"
        subdirectories (the road_data/ folder).
    category : str
        "driving" (6 sessions), "anomalies" (17 sessions), or "all" (23).
    session_idx : int or None
        Load a specific session index. None = all in category.
    with_gyro : bool
        Include gyroscope columns.
    with_magneto : bool
        Include magnetometer columns.

    Returns
    -------
    pd.DataFrame
        Columns: ts, lat, lon, speed_mps, ax_mps2, ay_mps2, az_mps2,
        [gx_rad_s, gy_rad_s, gz_rad_s], [mx_uT, my_uT, mz_uT],
        [altitude_gps_m, heading_deg, h_accuracy_m], device_id, trip_id
    """
    root = Path(source_path)

    # Collect session directories
    cat_dirs = []
    if category in ("driving", "all"):
        d = root / "Driving Behaviour"
        if d.exists():
            cat_dirs.append(d)
    if category in ("anomalies", "all"):
        d = root / "Road Anomalies"
        if d.exists():
            cat_dirs.append(d)
    if not cat_dirs:
        raise ValueError(f"Invalid category {category!r} or directory not found in {root}")

    sessions = []
    for cd in cat_dirs:
        for sub in sorted(cd.iterdir(), key=lambda p: p.name):
            if sub.is_dir():
                sessions.append(sub)

    if session_idx is not None:
        sessions = [sessions[session_idx]]

    dfs = []
    for sess in sessions:
        # --- Accelerometer (TotalAcceleration = raw with gravity) ---
        ta_path = sess / "TotalAcceleration.csv"
        if not ta_path.exists():
            continue
        ta = pd.read_csv(ta_path)
        ta["ts"] = pd.to_datetime(ta["time"], unit="ns", utc=True)
        ta = ta.rename(columns={"x": "ax_mps2", "y": "ay_mps2", "z": "az_mps2"})
        ta = ta[["ts", "ax_mps2", "ay_mps2", "az_mps2"]].sort_values("ts")

        # --- GPS (Location.csv) ---
        loc_path = sess / "Location.csv"
        if loc_path.exists():
            loc = pd.read_csv(loc_path)
            loc["ts"] = pd.to_datetime(loc["time"], unit="ns", utc=True)
            loc_cols = {"latitude": "lat", "longitude": "lon", "speed": "speed_mps"}
            loc = loc.rename(columns=loc_cols)

            keep = ["ts", "lat", "lon", "speed_mps"]
            if "altitude" in loc.columns:
                loc["altitude_gps_m"] = loc["altitude"].astype("float32")
                keep.append("altitude_gps_m")
            if "bearing" in loc.columns:
                loc["heading_deg"] = loc["bearing"].astype("float32")
                keep.append("heading_deg")
            if "horizontalAccuracy" in loc.columns:
                loc["h_accuracy_m"] = loc["horizontalAccuracy"].astype("float32")
                keep.append("h_accuracy_m")

            loc = loc[keep].sort_values("ts")
            m = pd.merge_asof(ta, loc, on="ts", direction="nearest")
        else:
            m = ta

        # --- Gyroscope (already rad/s) ---
        if with_gyro:
            gy_path = sess / "Gyroscope.csv"
            if gy_path.exists():
                gy = pd.read_csv(gy_path)
                gy["ts"] = pd.to_datetime(gy["time"], unit="ns", utc=True)
                gy = gy.rename(columns={"x": "gx_rad_s", "y": "gy_rad_s", "z": "gz_rad_s"})
                gy = gy[["ts", "gx_rad_s", "gy_rad_s", "gz_rad_s"]].sort_values("ts")
                m = pd.merge_asof(m, gy, on="ts", direction="nearest")

        # --- Magnetometer (already µT) ---
        if with_magneto:
            mag_path = sess / "Magnetometer.csv"
            if mag_path.exists():
                mag = pd.read_csv(mag_path)
                mag["ts"] = pd.to_datetime(mag["time"], unit="ns", utc=True)
                mag = mag.rename(columns={"x": "mx_uT", "y": "my_uT", "z": "mz_uT"})
                mag = mag[["ts", "mx_uT", "my_uT", "mz_uT"]].sort_values("ts")
                m = pd.merge_asof(m, mag, on="ts", direction="nearest")

        # --- Metadata ---
        m["trip_id"] = f"{sess.parent.name}/{sess.name}"
        m["device_id"] = "poco_x2"

        # Speed cleanup
        if "speed_mps" in m.columns:
            m["speed_mps"] = m["speed_mps"].fillna(0).clip(0, 50).astype("float32")

        dfs.append(m)

    if not dfs:
        raise FileNotFoundError(f"No STRIDE sessions found in {root}")

    result = pd.concat(dfs, ignore_index=True)
    result = result.dropna(subset=["ax_mps2", "ay_mps2", "az_mps2"])
    if "lat" in result.columns:
        result = result.dropna(subset=["lat", "lon"])
    return result.reset_index(drop=True)
