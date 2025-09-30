

# tests/test_core_negative.py
# Negative tests for Telemachus core validators

import pandas as pd
import pytest

from telemachus.core.errors import SemanticError, UnitsError
from telemachus.core.validate_tables import (
    validate_trajectory_df,
    validate_imu_df,
    validate_events_df,
)
from telemachus.core.semantics import assert_units, check_alignment


def test_invalid_lat_lon_out_of_bounds():
    df = pd.DataFrame({
        "timestamp_ns": [1, 2, 3],
        "lat": [0.0, 95.0, 10.0],  # invalid latitude > 90
        "lon": [0.0, 0.0, 0.0],
        "speed_mps": [1.0, 2.0, 3.0],
        "alt": [10.0, 10.0, 10.0],
    })
    with pytest.raises(SemanticError):
        validate_trajectory_df(df)


def test_non_monotonic_timestamps_imu():
    df = pd.DataFrame({
        "timestamp_ns": [1, 3, 2],  # not strictly increasing
        "acc_x": [0.0, 0.0, 0.0],
        "acc_y": [0.0, 0.0, 0.0],
        "acc_z": [9.81, 9.81, 9.81],
        "gyro_x": [0.0, 0.0, 0.0],
        "gyro_y": [0.0, 0.0, 0.0],
        "gyro_z": [0.0, 0.0, 0.0],
    })
    with pytest.raises(SemanticError):
        validate_imu_df(df)


def test_units_mismatch_raises():
    bad_units = {"speed": "km/h", "acceleration": "m/s^2", "gyro": "rad/s"}
    with pytest.raises(UnitsError):
        assert_units(bad_units)


def test_alignment_exceeds_tolerance_warns():
    traj = pd.DataFrame({
        "timestamp_ns": [1_000_000, 2_000_000, 3_000_000],
        "lat": [0.0, 0.0, 0.0],
        "lon": [0.0, 0.0, 0.0],
        "speed_mps": [1.0, 1.0, 1.0],
    })
    imu = pd.DataFrame({
        "timestamp_ns": [10_000_000, 20_000_000, 30_000_000],  # far apart
        "acc_x": [0.0, 0.0, 0.0],
        "acc_y": [0.0, 0.0, 0.0],
        "acc_z": [9.81, 9.81, 9.81],
        "gyro_x": [0.0, 0.0, 0.0],
        "gyro_y": [0.0, 0.0, 0.0],
        "gyro_z": [0.0, 0.0, 0.0],
    })
    # By default should only warn, not raise; we don't assert on warnings here
    metrics = check_alignment(traj, imu, tolerance_ns=1_000)
    assert metrics["exceeds"] > 0


def test_events_null_event_type_raises():
    df = pd.DataFrame({
        "timestamp_ns": [1, 2],
        "event_type": ["brake", None],  # null not allowed
        "severity": [1, 2],
        "meta": ["{}", "{}"],
    })
    with pytest.raises(SemanticError):
        validate_events_df(df)