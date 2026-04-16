

import os
import tempfile
import pandas as pd

from telemachus.io_export import export_rs3_to_telemachus
from telemachus._validate_legacy import validate_manifest, summarize_dataset


def _make_minimal_rs3_csvs(tmpdir: str):
    """Create tiny RS3-like CSV files for trajectory/imu/events and return their paths."""
    traj_path = os.path.join(tmpdir, "traj.csv")
    imu_path = os.path.join(tmpdir, "imu.csv")
    ev_path = os.path.join(tmpdir, "events.csv")

    # Minimal trajectory: timestamp (ISO), lat, lon, speed (m/s), optional alt
    traj = pd.DataFrame({
        "timestamp": ["2025-09-30T10:00:00Z", "2025-09-30T10:00:00.1Z", "2025-09-30T10:00:00.2Z"],
        "lat": [48.8566, 48.85661, 48.85662],
        "lon": [2.3522, 2.35221, 2.35222],
        "speed": [10.0, 10.2, 10.4],
        "alt": [35.0, 35.1, 35.2],
    })
    traj.to_csv(traj_path, index=False)

    # Minimal IMU: timestamp (ISO), accelerations, gyros
    imu = pd.DataFrame({
        "timestamp": ["2025-09-30T10:00:00Z", "2025-09-30T10:00:00.1Z", "2025-09-30T10:00:00.2Z"],
        "acc_x": [0.1, 0.1, 0.1],
        "acc_y": [0.0, 0.0, 0.0],
        "acc_z": [9.81, 9.81, 9.81],
        "gyro_x": [0.001, 0.001, 0.001],
        "gyro_y": [0.0, 0.0, 0.0],
        "gyro_z": [0.0, 0.0, 0.0],
    })
    imu.to_csv(imu_path, index=False)

    # Minimal events
    ev = pd.DataFrame({
        "timestamp": ["2025-09-30T10:00:00.15Z"],
        "event_type": ["turn_left"],
        "severity": [1],
        "meta": ["{}"],
    })
    ev.to_csv(ev_path, index=False)

    return traj_path, imu_path, ev_path


def test_validate_roundtrip_minimal():
    with tempfile.TemporaryDirectory() as tmp:
        traj_csv, imu_csv, ev_csv = _make_minimal_rs3_csvs(tmp)
        outdir = os.path.join(tmp, "out")

        export_rs3_to_telemachus(
            traj_csv=traj_csv,
            imu_csv=imu_csv,
            events_csv=ev_csv,
            outdir=outdir,
            freq_hz=10,
            vehicle_id="VEH-TEST",
            vehicle_type="passenger_car",
        )

        manifest_path = os.path.join(outdir, "dataset.yaml")
        ok, report = validate_manifest(manifest_path)
        assert ok, report


def test_info_summary_smoke():
    with tempfile.TemporaryDirectory() as tmp:
        traj_csv, imu_csv, ev_csv = _make_minimal_rs3_csvs(tmp)
        outdir = os.path.join(tmp, "out")

        export_rs3_to_telemachus(
            traj_csv=traj_csv,
            imu_csv=imu_csv,
            events_csv=ev_csv,
            outdir=outdir,
            freq_hz=10,
            vehicle_id="VEH-TEST",
            vehicle_type="passenger_car",
        )

        manifest_path = os.path.join(outdir, "dataset.yaml")
        summary = summarize_dataset(manifest_path)
        # basic smoke checks
        assert "Dataset:" in summary
        assert "trajectory" in summary
        assert "imu" in summary
        assert "events" in summary