"""
PVS adapter — Kaggle (Curitiba, Brazil).

MPU-9250 research platform: 100 Hz accel+gyro+magneto, 1 Hz GPS.
3 placements × 2 sides per trip, 9 trips × 3 vehicles.
Raw units: m/s² (accel), deg/s (gyro), µT (magneto), decimal degrees (GPS).

Reference: CC-BY-NC-ND-4.0 (data not redistributable)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

DEG2RAD = np.pi / 180.0


def load(
    source_path: str | Path,
    *,
    trip_idx: Optional[int] = None,
    placement: str = "dashboard",
    side: str = "left",
) -> pd.DataFrame:
    """Load PVS dataset and return a Telemachus-conformant DataFrame.

    Parameters
    ----------
    source_path : str or Path
        Directory containing trip subdirectories (PVS 1, PVS 2, ...).
    trip_idx : int or None
        Load a specific trip (1-9). None = all.
    placement : str
        "dashboard", "above_suspension", or "below_suspension".
    side : str
        "left" or "right" (MPU sensor selection).

    Returns
    -------
    pd.DataFrame
        Columns: ts, lat, lon, speed_mps, ax_mps2, ay_mps2, az_mps2,
        gx_rad_s, gy_rad_s, gz_rad_s, mx_uT, my_uT, mz_uT,
        [altitude_gps_m, hdop, n_satellites], device_id, trip_id
    """
    root = Path(source_path)

    # Find trip directories
    trip_dirs = sorted(
        [d for d in root.iterdir() if d.is_dir() and d.name.startswith("PVS")],
        key=lambda d: int(d.name.split()[-1]) if d.name.split()[-1].isdigit() else 0,
    )
    if trip_idx is not None:
        trip_dirs = [trip_dirs[trip_idx - 1]]

    dfs = []
    for trip_dir in trip_dirs:
        csv_path = trip_dir / f"dataset_gps_mpu_{side}.csv"
        if not csv_path.exists():
            continue

        df = pd.read_csv(csv_path)
        df["ts"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

        # Acceleration (already m/s²)
        df["ax_mps2"] = df[f"acc_x_{placement}"].astype("float32")
        df["ay_mps2"] = df[f"acc_y_{placement}"].astype("float32")
        df["az_mps2"] = df[f"acc_z_{placement}"].astype("float32")

        # Gyroscope: deg/s → rad/s
        df["gx_rad_s"] = (df[f"gyro_x_{placement}"] * DEG2RAD).astype("float32")
        df["gy_rad_s"] = (df[f"gyro_y_{placement}"] * DEG2RAD).astype("float32")
        df["gz_rad_s"] = (df[f"gyro_z_{placement}"] * DEG2RAD).astype("float32")

        # Magnetometer (µT, direct)
        mag_col = f"mag_x_{placement}"
        if mag_col in df.columns:
            df["mx_uT"] = df[f"mag_x_{placement}"].astype("float32")
            df["my_uT"] = df[f"mag_y_{placement}"].astype("float32")
            df["mz_uT"] = df[f"mag_z_{placement}"].astype("float32")

        # GPS (decimal degrees, direct)
        df["lat"] = df["latitude"]
        df["lon"] = df["longitude"]
        df["speed_mps"] = df["speed"].fillna(0).clip(0, 50).astype("float32")

        # GPS metadata from separate GPS CSV if available
        gps_csv = trip_dir / "dataset_gps.csv"
        if gps_csv.exists():
            gps = pd.read_csv(gps_csv)
            gps["ts_gps"] = pd.to_datetime(gps["timestamp"], unit="s", utc=True)
            if "elevation" in gps.columns:
                gps_meta = gps[["ts_gps"]].copy()
                if "elevation" in gps.columns:
                    gps_meta["altitude_gps_m"] = gps["elevation"].astype("float32")
                if "hdop" in gps.columns:
                    gps_meta["hdop"] = gps["hdop"].astype("float32")
                if "satellites" in gps.columns:
                    gps_meta["n_satellites"] = gps["satellites"]
                gps_meta = gps_meta.sort_values("ts_gps")
                df = df.sort_values("ts")
                df = pd.merge_asof(df, gps_meta, left_on="ts", right_on="ts_gps", direction="nearest")

        # Metadata
        df["trip_id"] = trip_dir.name.replace(" ", "_")
        df["device_id"] = f"pvs_{side}"

        # Select columns
        cols = ["ts", "lat", "lon", "speed_mps", "ax_mps2", "ay_mps2", "az_mps2",
                "gx_rad_s", "gy_rad_s", "gz_rad_s"]
        for opt in ["mx_uT", "my_uT", "mz_uT", "altitude_gps_m", "hdop", "n_satellites"]:
            if opt in df.columns:
                cols.append(opt)
        cols += ["device_id", "trip_id"]
        df = df[[c for c in cols if c in df.columns]]

        dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No PVS trip data found in {root}")

    result = pd.concat(dfs, ignore_index=True)
    result = result.dropna(subset=["ax_mps2", "ay_mps2", "az_mps2", "lat", "lon"])
    return result.reset_index(drop=True)
