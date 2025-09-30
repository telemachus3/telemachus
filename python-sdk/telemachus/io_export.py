

"""
Export utilities to build a Telemachus dataset (v0.1) from RS3 CSV files.

This module creates:
- Parquet tables under <outdir>/tables/
- A YAML manifest at <outdir>/dataset.yaml

Expected RS3 CSV columns:
- trajectory CSV: timestamp, lat, lon, speed[, alt]
- imu CSV:        timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
- events CSV:     timestamp, event_type[, severity, meta]

Conventions:
- Common clock: UTC nanoseconds in column `timestamp_ns:int64`
- Units: speed m/s, acceleration m/s^2, gyroscope rad/s
- CRS: EPSG:4326
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


def _to_ns(ts) -> int:
    """Convert timestamp (ISO8601 string or numeric) to UTC nanoseconds (int)."""
    if isinstance(ts, (int, float)):
        return int(ts)
    # let pandas parse ISO8601 and ensure UTC
    return int(pd.to_datetime(ts, utc=True).value)


def _write_parquet(df: pd.DataFrame, path: str) -> None:
    """Write a DataFrame to Parquet (zstd compression), ensuring parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, compression="zstd")


def export_rs3_to_telemachus(
    traj_csv: str,
    imu_csv: str,
    events_csv: Optional[str],
    outdir: str,
    freq_hz: int = 10,
    vehicle_id: str = "VEH-01",
    vehicle_type: str = "passenger_car",
) -> None:
    """
    Export RS3 CSV files to a Telemachus dataset directory.

    Args:
        traj_csv: Path to RS3 trajectory CSV (timestamp,lat,lon,alt?,speed)
        imu_csv: Path to RS3 IMU CSV (timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z)
        events_csv: Optional path to events CSV (timestamp,event_type,severity?,meta?)
        outdir: Output directory for the Telemachus dataset
        freq_hz: Nominal frequency in Hz
        vehicle_id: Vehicle opaque identifier
        vehicle_type: Vehicle category

    Produces:
        <outdir>/dataset.yaml
        <outdir>/tables/trajectory.parquet
        <outdir>/tables/imu.parquet
        <outdir>/tables/events.parquet
    """
    tables_dir = os.path.join(outdir, "tables")
    os.makedirs(tables_dir, exist_ok=True)

    # ---- trajectory ----
    traj = pd.read_csv(traj_csv)
    # normalize column names
    if "speed" in traj.columns:
        traj = traj.rename(columns={"speed": "speed_mps"})
    if "timestamp_ns" not in traj.columns:
        traj["timestamp_ns"] = traj["timestamp"].apply(_to_ns)

    traj_cols = ["timestamp_ns", "lat", "lon", "speed_mps"]
    if "alt" in traj.columns:
        traj_cols.insert(3, "alt")  # after lon, before speed_mps
    # keep only expected columns if present
    traj = traj[[c for c in traj_cols if c in traj.columns]]
    _write_parquet(traj, os.path.join(tables_dir, "trajectory.parquet"))

    # ---- imu ----
    imu = pd.read_csv(imu_csv)
    if "timestamp_ns" not in imu.columns:
        imu["timestamp_ns"] = imu["timestamp"].apply(_to_ns)
    imu = imu[["timestamp_ns", "acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"]]
    _write_parquet(imu, os.path.join(tables_dir, "imu.parquet"))

    # ---- events (optional, create empty table if absent) ----
    events_path = os.path.join(tables_dir, "events.parquet")
    if events_csv and os.path.exists(events_csv):
        ev = pd.read_csv(events_csv)
        if "timestamp_ns" not in ev.columns:
            ev["timestamp_ns"] = ev["timestamp"].apply(_to_ns)
        if "severity" not in ev.columns:
            ev["severity"] = pd.NA
        if "meta" not in ev.columns:
            ev["meta"] = pd.NA
        ev = ev[["timestamp_ns", "event_type", "severity", "meta"]]
        _write_parquet(ev, events_path)
    else:
        empty = pd.DataFrame(columns=["timestamp_ns", "event_type", "severity", "meta"])
        _write_parquet(empty, events_path)

    # ---- manifest YAML ----
    manifest = {
        "version": "0.1.0",
        "dataset_id": f"tele-{int(time.time())}",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "producer": "RoadSimulator3",
        "frequency_hz": int(freq_hz),
        "crs": "EPSG:4326",
        "units": {"speed": "m/s", "acceleration": "m/s^2", "gyro": "rad/s"},
        "vehicle": {"id": vehicle_id, "type": vehicle_type},
        "source": {"route_engine": "OSRM-car"},
        "tables": [
            {"name": "trajectory", "format": "parquet", "path": "tables/trajectory.parquet"},
            {"name": "imu", "format": "parquet", "path": "tables/imu.parquet"},
            {"name": "events", "format": "parquet", "path": "tables/events.parquet"},
        ],
    }

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "dataset.yaml"), "w") as f:
        yaml.dump(manifest, f, sort_keys=False)