import os
from pathlib import Path

import pytest

from telemachus.core.dataset import Dataset


def test_dataset_manifest_load_and_summary(tmp_path: Path, monkeypatch):
    """
    Synthetic minimal manifest + empty parquet tables.
    Note: we only check plumbing here; deep schema validation is in bridge tests.
    """
    # fake files (empty parquet files are allowed for plumbing checks)
    (tmp_path / "tables").mkdir()
    (tmp_path / "tables" / "traj.parquet").touch()
    (tmp_path / "tables" / "imu.parquet").touch()

    manifest = {
        "name": "demo",
        "version": "0.1",
        "dataset_id": "demo-000",
        "created_utc": "2025-01-01T00:00:00Z",
        "producer": "tests",
        "frequency_hz": 10,
        "vehicle": {"id": "VL-TEST", "type": "van"},
        "tables": [
            {"name": "trajectory", "format": "parquet", "path": "tables/traj.parquet"},
            {"name": "imu", "format": "parquet", "path": "tables/imu.parquet"},
        ],
    }
    mpath = tmp_path / "dataset.yaml"
    mpath.write_text(__import__("yaml").safe_dump(manifest), encoding="utf-8")

    ds = Dataset.from_manifest(mpath)
    assert "trajectory" in ds.tables
    assert "imu" in ds.tables

    # summary should not fail even if tables are empty
    s = ds.summary()
    assert isinstance(s, dict)