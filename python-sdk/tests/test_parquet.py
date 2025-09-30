# tests/test_parquet.py
# Modern test aligned with Telemachus v0.1 (manifest YAML + Parquet tables)

import os
import pandas as pd
import pyarrow.parquet as pq

from telemachus.io_export import export_rs3_to_telemachus


def test_parquet_roundtrip_modern(tmp_path):
    # Create minimal RS3-like CSV inputs
    traj_csv = tmp_path / "trajectory.csv"
    pd.DataFrame({
        "timestamp": ["2025-01-01T00:00:00Z"],
        "lat": [48.8566],
        "lon": [2.3522],
        "speed": [10.0],
    }).to_csv(traj_csv, index=False)

    imu_csv = tmp_path / "imu.csv"
    pd.DataFrame({
        "timestamp": ["2025-01-01T00:00:00Z"],
        "acc_x": [0.1],
        "acc_y": [0.0],
        "acc_z": [9.81],
        "gyro_x": [0.001],
        "gyro_y": [0.0],
        "gyro_z": [0.0],
    }).to_csv(imu_csv, index=False)

    events_csv = tmp_path / "events.csv"
    pd.DataFrame({
        "timestamp": ["2025-01-01T00:00:00Z"],
        "event_type": ["start"],
    }).to_csv(events_csv, index=False)

    # Export to Telemachus dataset (writes Parquet files under outdir/tables)
    outdir = tmp_path / "out"
    export_rs3_to_telemachus(
        traj_csv=str(traj_csv),
        imu_csv=str(imu_csv),
        events_csv=str(events_csv),
        outdir=str(outdir),
        freq_hz=10,
        vehicle_id="VEH-TEST",
        vehicle_type="passenger_car",
    )

    # Read back one of the Parquet tables (trajectory) and verify content
    traj_parquet = outdir / "tables/trajectory.parquet"
    pf = pq.ParquetFile(traj_parquet)
    assert pf.metadata.num_rows == 1
    df = pf.read().to_pandas()
    assert set(["timestamp_ns", "lat", "lon", "speed_mps"]).issubset(df.columns)