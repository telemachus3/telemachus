# tests/test_dataset.py
# Modern test aligned with Telemachus v0.1 (manifest YAML + Parquet tables)

import os
import tempfile
import pandas as pd

from telemachus.io_export import export_rs3_to_telemachus
from telemachus.validate import validate_manifest, summarize_dataset


def test_dataset_flow_modern():
    with tempfile.TemporaryDirectory() as tmp:
        # Create minimal RS3-like CSV inputs
        traj_csv = os.path.join(tmp, "trajectory.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00Z", "2025-01-01T00:00:00.1Z"],
            "lat": [48.8566, 48.85661],
            "lon": [2.3522, 2.35221],
            "speed": [10.0, 10.2],
        }).to_csv(traj_csv, index=False)

        imu_csv = os.path.join(tmp, "imu.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00Z", "2025-01-01T00:00:00.1Z"],
            "acc_x": [0.1, 0.1],
            "acc_y": [0.0, 0.0],
            "acc_z": [9.81, 9.81],
            "gyro_x": [0.001, 0.001],
            "gyro_y": [0.0, 0.0],
            "gyro_z": [0.0, 0.0],
        }).to_csv(imu_csv, index=False)

        events_csv = os.path.join(tmp, "events.csv")
        pd.DataFrame({
            "timestamp": ["2025-01-01T00:00:00.05Z"],
            "event_type": ["start"],
        }).to_csv(events_csv, index=False)

        # Export to Telemachus dataset
        outdir = os.path.join(tmp, "out")
        export_rs3_to_telemachus(
            traj_csv=traj_csv,
            imu_csv=imu_csv,
            events_csv=events_csv,
            outdir=outdir,
            freq_hz=10,
            vehicle_id="VEH-TEST",
            vehicle_type="passenger_car",
        )

        manifest_path = os.path.join(outdir, "dataset.yaml")

        # Validate manifest + Parquet tables
        ok, report = validate_manifest(manifest_path)
        assert ok, report

        # Summarize dataset
        summary = summarize_dataset(manifest_path)
        assert "trajectory" in summary and "imu" in summary and "events" in summary