"""Tests for the adapter framework and validation of adapter output."""

import numpy as np
import pandas as pd
import pytest

import telemachus as tele
from telemachus.adapters import REGISTRY, load as adapter_load


def test_registry_contains_all_adapters():
    assert "aegis" in REGISTRY
    assert "pvs" in REGISTRY
    assert "stride" in REGISTRY


def test_unknown_adapter_raises():
    with pytest.raises(ValueError, match="Unknown adapter"):
        adapter_load("nonexistent", "/tmp")


def _make_synthetic_imu_df(n=100, with_gyro=False, with_magneto=False):
    """Create a synthetic Telemachus-conformant DataFrame for testing."""
    df = pd.DataFrame({
        "ts": pd.date_range("2025-01-01", periods=n, freq="100ms", tz="UTC"),
        "lat": [49.33 + i * 0.0001 if i % 10 == 0 else np.nan for i in range(n)],
        "lon": [1.38 + i * 0.0001 if i % 10 == 0 else np.nan for i in range(n)],
        "speed_mps": np.array([5.0 if i % 10 == 0 else np.nan for i in range(n)], dtype="float32"),
        "ax_mps2": np.random.randn(n).astype("float32") * 0.5,
        "ay_mps2": np.random.randn(n).astype("float32") * 0.3,
        "az_mps2": (9.81 + np.random.randn(n) * 0.1).astype("float32"),
        "device_id": "test_device",
        "trip_id": "trip_001",
    })
    if with_gyro:
        df["gx_rad_s"] = np.random.randn(n).astype("float32") * 0.01
        df["gy_rad_s"] = np.random.randn(n).astype("float32") * 0.01
        df["gz_rad_s"] = np.random.randn(n).astype("float32") * 0.01
    if with_magneto:
        df["mx_uT"] = np.random.randn(n).astype("float32") * 10
        df["my_uT"] = np.random.randn(n).astype("float32") * 10
        df["mz_uT"] = np.random.randn(n).astype("float32") * 10
    return df


class TestValidation:
    """Test validation on synthetic data matching adapter output format."""

    def test_imu_profile_valid(self):
        df = _make_synthetic_imu_df()
        report = tele.validate(df, profile="imu")
        assert report.ok, str(report)
        assert report.profile == "imu"

    def test_core_profile_valid(self):
        df = _make_synthetic_imu_df()
        core_df = df[["ts", "lat", "lon", "speed_mps"]].copy()
        report = tele.validate(core_df, profile="core")
        assert report.ok, str(report)

    def test_full_profile_valid(self):
        df = _make_synthetic_imu_df(with_gyro=True)
        report = tele.validate(df, profile="full")
        assert report.ok, str(report)

    def test_full_profile_missing_gyro_fails(self):
        df = _make_synthetic_imu_df(with_gyro=False)
        report = tele.validate(df, profile="full")
        assert not report.ok
        assert any("Missing mandatory" in e for e in report.errors)

    def test_partial_gyro_fails(self):
        df = _make_synthetic_imu_df()
        df["gx_rad_s"] = 0.0  # only one of three
        report = tele.validate(df)
        assert not report.ok
        assert any("Partial gyro" in e for e in report.errors)

    def test_partial_magneto_fails(self):
        df = _make_synthetic_imu_df()
        df["mx_uT"] = 0.0  # only one of three
        report = tele.validate(df)
        assert not report.ok
        assert any("Partial magneto" in e for e in report.errors)

    def test_heading_out_of_range(self):
        df = _make_synthetic_imu_df()
        df["heading_deg"] = 400.0  # out of [0, 360)
        report = tele.validate(df)
        assert not report.ok
        assert any("heading_deg" in e for e in report.errors)

    def test_negative_speed_fails(self):
        df = _make_synthetic_imu_df()
        df.loc[0, "speed_mps"] = -1.0
        report = tele.validate(df)
        assert not report.ok

    def test_auto_detect_profile(self):
        df_imu = _make_synthetic_imu_df()
        assert tele.validate(df_imu).profile == "imu"

        df_full = _make_synthetic_imu_df(with_gyro=True)
        assert tele.validate(df_full).profile == "full"

        df_core = df_imu[["ts", "lat", "lon", "speed_mps"]].copy()
        assert tele.validate(df_core).profile == "core"


class TestIntrospection:
    def test_sensor_profile_imu(self):
        df = _make_synthetic_imu_df()
        assert tele.sensor_profile(df) == "gps+imu"

    def test_sensor_profile_full(self):
        df = _make_synthetic_imu_df(with_gyro=True, with_magneto=True)
        assert tele.sensor_profile(df) == "gps+imu+gyro+magneto"

    def test_is_gps_only(self):
        df = _make_synthetic_imu_df()
        core_df = df[["ts", "lat", "lon", "speed_mps"]].copy()
        assert tele.is_gps_only(core_df)
        assert not tele.is_gps_only(df)

    def test_is_full_imu(self):
        df = _make_synthetic_imu_df(with_gyro=True)
        assert tele.is_full_imu(df)
        df_no_gyro = _make_synthetic_imu_df()
        assert not tele.is_full_imu(df_no_gyro)
