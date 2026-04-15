

import os
import tempfile
import pandas as pd
import pyarrow.parquet as pq

from telemachus.io_export import export_rs3_to_telemachus


def _make_minimal_rs3_csvs(tmpdir: str, with_events: bool = True):
    traj_path = os.path.join(tmpdir, "traj.csv")
    imu_path = os.path.join(tmpdir, "imu.csv")
    ev_path = os.path.join(tmpdir, "events.csv")

    # trajectory CSV (with alt column)
    pd.DataFrame({
        "timestamp": [
            "2025-09-30T10:00:00Z",
            "2025-09-30T10:00:00.1Z",
            "2025-09-30T10:00:00.2Z",
        ],
        "lat": [48.8566, 48.85661, 48.85662],
        "lon": [2.3522, 2.35221, 2.35222],
        "alt": [35.0, 35.1, 35.2],
        "speed": [10.0, 10.2, 10.4],
    }).to_csv(traj_path, index=False)

    # imu CSV
    pd.DataFrame({
        "timestamp": [
            "2025-09-30T10:00:00Z",
            "2025-09-30T10:00:00.1Z",
            "2025-09-30T10:00:00.2Z",
        ],
        "acc_x": [0.1, 0.1, 0.1],
        "acc_y": [0.0, 0.0, 0.0],
        "acc_z": [9.81, 9.81, 9.81],
        "gyro_x": [0.001, 0.001, 0.001],
        "gyro_y": [0.0, 0.0, 0.0],
        "gyro_z": [0.0, 0.0, 0.0],
    }).to_csv(imu_path, index=False)

    if with_events:
        pd.DataFrame({
            "timestamp": ["2025-09-30T10:00:00.15Z"],
            "event_type": ["turn_left"],
            "severity": [1],
            "meta": ["{}"],
        }).to_csv(ev_path, index=False)
        return traj_path, imu_path, ev_path
    else:
        return traj_path, imu_path, ""


def test_export_tables_exist_and_readable():
    with tempfile.TemporaryDirectory() as tmp:
        traj_csv, imu_csv, ev_csv = _make_minimal_rs3_csvs(tmp, with_events=True)
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

        # Parquet files should exist and be readable
        for rel in [
            "tables/trajectory.parquet",
            "tables/imu.parquet",
            "tables/events.parquet",
        ]:
            p = os.path.join(outdir, rel)
            assert os.path.exists(p)
            pq.ParquetFile(p)  # should not raise


def test_export_without_events_creates_empty_table():
    with tempfile.TemporaryDirectory() as tmp:
        traj_csv, imu_csv, ev_csv = _make_minimal_rs3_csvs(tmp, with_events=False)
        outdir = os.path.join(tmp, "out")

        export_rs3_to_telemachus(
            traj_csv=traj_csv,
            imu_csv=imu_csv,
            events_csv=ev_csv,  # empty path
            outdir=outdir,
            freq_hz=10,
            vehicle_id="VEH-TEST",
            vehicle_type="passenger_car",
        )

        events_path = os.path.join(outdir, "tables/events.parquet")
        assert os.path.exists(events_path)
        pf = pq.ParquetFile(events_path)
        assert pf.metadata.num_rows == 0  # empty table created