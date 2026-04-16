"""
AEGIS adapter — Zenodo 820576 (Graz, Austria).

BeagleBone-based research platform: 24 Hz accel+gyro, 5 Hz GPS, OBD.
Raw units: G-force (accel), deg/s (gyro), NMEA DDMM.MMMM (GPS).

Reference: Brunner et al. (2017), CC-BY-4.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

G = 9.80665
DEG2RAD = np.pi / 180.0


def _nmea_to_decimal(nmea_val: float) -> float:
    """Convert NMEA DDMM.MMMM to decimal degrees."""
    degrees = int(nmea_val / 100)
    minutes = nmea_val - degrees * 100
    return degrees + minutes / 60.0


def load(
    source_path: str | Path,
    *,
    top_n_trips: Optional[int] = 5,
    with_gyro: bool = True,
    with_obd: bool = False,
) -> pd.DataFrame:
    """Load AEGIS dataset and return a Telemachus-conformant DataFrame.

    Parameters
    ----------
    source_path : str or Path
        Directory containing accelerations.csv, positions.csv,
        gyroscopes.csv, obdData.csv, trips.csv.
    top_n_trips : int or None
        Load N longest trips (by duration). None = all.
    with_gyro : bool
        Include gyroscope columns.
    with_obd : bool
        Include OBD speed (PID 0x0D).

    Returns
    -------
    pd.DataFrame
        Columns: ts, lat, lon, speed_mps, ax_mps2, ay_mps2, az_mps2,
        [gx_rad_s, gy_rad_s, gz_rad_s], [speed_obd_mps],
        altitude_gps_m, device_id, trip_id
    """
    root = Path(source_path)

    # --- Load CSV files ---
    acc = pd.read_csv(root / "accelerations.csv")
    pos = pd.read_csv(root / "positions.csv")
    trips = pd.read_csv(root / "trips.csv")

    # --- Trip selection ---
    if top_n_trips is not None:
        # Select longest trips by row count in accelerations
        trip_counts = acc["trip_id"].value_counts().nlargest(top_n_trips)
        selected_trips = set(trip_counts.index)
        acc = acc[acc["trip_id"].isin(selected_trips)]
        pos = pos[pos["trip_id"].isin(selected_trips)]

    # --- Accelerations: G-force → m/s² ---
    acc["ts"] = pd.to_datetime(acc["timestamp"], utc=True, errors="coerce")
    acc["ax_mps2"] = acc["x_value"].astype("float32") * G
    acc["ay_mps2"] = acc["y_value"].astype("float32") * G
    acc["az_mps2"] = acc["z_value"].astype("float32") * G
    acc["trip_id"] = acc["trip_id"].astype(str)
    acc = acc[["ts", "ax_mps2", "ay_mps2", "az_mps2", "trip_id"]].sort_values("ts")

    # --- GPS: NMEA → decimal degrees ---
    pos["ts"] = pd.to_datetime(pos["timestamp"], utc=True, errors="coerce")
    pos["lat"] = pos["latitude"].apply(_nmea_to_decimal)
    pos["lon"] = pos["longitude"].apply(_nmea_to_decimal)
    pos["altitude_gps_m"] = pos["altitude"].astype("float32")
    pos = pos[["ts", "lat", "lon", "altitude_gps_m"]].sort_values("ts")

    # --- Merge accel + GPS (multi-rate) ---
    df = pd.merge_asof(acc, pos, on="ts", direction="nearest")

    # --- Gyroscope: deg/s → rad/s ---
    if with_gyro:
        gyro = pd.read_csv(root / "gyroscopes.csv")
        gyro["ts"] = pd.to_datetime(gyro["timestamp"], utc=True, errors="coerce")
        gyro["gx_rad_s"] = gyro["x_value"].astype("float32") * DEG2RAD
        gyro["gy_rad_s"] = gyro["y_value"].astype("float32") * DEG2RAD
        gyro["gz_rad_s"] = gyro["z_value"].astype("float32") * DEG2RAD
        if top_n_trips is not None:
            gyro = gyro[gyro["trip_id"].isin(selected_trips)]
        gyro = gyro[["ts", "gx_rad_s", "gy_rad_s", "gz_rad_s"]].sort_values("ts")
        df = pd.merge_asof(df, gyro, on="ts", direction="nearest")

    # --- OBD speed: km/h → m/s ---
    if with_obd:
        obd = pd.read_csv(root / "obdData.csv")
        obd_speed = obd[obd["obdPid"] == "0D"].copy()
        obd_speed["ts"] = pd.to_datetime(obd_speed["timestamp"], utc=True, errors="coerce")
        obd_speed["speed_obd_mps"] = pd.to_numeric(obd_speed["data"], errors="coerce") / 3.6
        if top_n_trips is not None:
            obd_speed = obd_speed[obd_speed["trip_id"].isin(selected_trips)]
        obd_speed = obd_speed[["ts", "speed_obd_mps"]].sort_values("ts")
        df = pd.merge_asof(df, obd_speed, on="ts", direction="nearest")

    # --- GPS-derived speed (fallback) ---
    # Compute haversine speed from lat/lon differences
    lat_r = np.radians(df["lat"].to_numpy())
    lon_r = np.radians(df["lon"].to_numpy())
    dt = df["ts"].diff().dt.total_seconds().to_numpy()

    dlat = np.diff(lat_r, prepend=lat_r[0])
    dlon = np.diff(lon_r, prepend=lon_r[0])
    a = np.sin(dlat / 2) ** 2 + np.cos(lat_r) * np.cos(np.roll(lat_r, 1)) * np.sin(dlon / 2) ** 2
    dist = 2 * 6_371_000 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    with np.errstate(divide="ignore", invalid="ignore"):
        speed = dist / dt
    speed[0] = np.nan
    speed[~np.isfinite(speed)] = np.nan
    df["speed_mps"] = speed.astype("float32")

    # --- Device ID from trips table ---
    trip_device = trips.set_index("trip_id")["beaglebone_id"].to_dict()
    df["device_id"] = df["trip_id"].map(
        lambda t: str(trip_device.get(int(t), "unknown")) if t.isdigit() else "unknown"
    )

    # --- Cleanup ---
    df = df.dropna(subset=["ax_mps2", "ay_mps2", "az_mps2", "lat", "lon"])
    df = df.reset_index(drop=True)

    return df
