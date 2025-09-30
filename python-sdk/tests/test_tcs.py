# tests/test_tcs.py
# Modern test aligned with Telemachus v0.1 (manifest YAML + Parquet tables)

import os
import tempfile
import pandas as pd

from telemachus.io_export import export_rs3_to_telemachus
from telemachus.validate import validate_manifest, summarize_dataset


def test_tcs_dataset_summary_modern():
    with tempfile.TemporaryDirectory() as tmp:
        # Minimal trajectory with missing optional altitude
        traj_csv = os.path.join(tmp, "trajectory.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00Z"],
            "lat": [48.85],
            "lon": [2.35],
            "speed": [12.3],
        }).to_csv(traj_csv, index=False)

        imu_csv = os.path.join(tmp, "imu.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00Z"],
            "acc_x": [0.1],
            "acc_y": [0.0],
            "acc_z": [9.81],
            "gyro_x": [0.0],
            "gyro_y": [0.0],
            "gyro_z": [0.0],
        }).to_csv(imu_csv, index=False)

        events_csv = os.path.join(tmp, "events.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00Z"],
            "event_type": ["brake"],
        }).to_csv(events_csv, index=False)

        outdir = os.path.join(tmp, "out")
        export_rs3_to_telemachus(
            traj_csv=traj_csv,
            imu_csv=imu_csv,
            events_csv=events_csv,
            outdir=outdir,
            freq_hz=10,
            vehicle_id="V1",
            vehicle_type="passenger_car",
        )

        manifest_path = os.path.join(outdir, "dataset.yaml")

        ok, report = validate_manifest(manifest_path)
        assert ok, report

        summary = summarize_dataset(manifest_path)
        assert "trajectory" in summary
        assert "imu" in summary
        assert "events" in summary