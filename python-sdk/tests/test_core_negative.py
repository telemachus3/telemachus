

# tests/test_core_negative.py
# Negative tests for Telemachus core validators

import numpy as np
import pandas as pd
import pytest

import telemachus as tele
from telemachus.core.errors import SemanticError, UnitsError
from telemachus.core.semantics import AlignmentWarning, assert_units, check_alignment
from telemachus.core.validate_tables import (
    validate_events_df,
    validate_imu_df,
    validate_trajectory_df,
)


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
    # By default should only warn, not raise; we check warnings here
    with pytest.warns(AlignmentWarning):
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

# ---------------------------------------------------------------------------
# SPEC-01 §2.3.1: a receiver that measures no speed
# ---------------------------------------------------------------------------

def _positions_only(n=50):
    return pd.DataFrame({
        "ts": pd.date_range("2026-01-01", periods=n, freq="1s", tz="UTC"),
        "lat": 49.33 + np.arange(n) * 1e-5,
        "lon": 1.38 + np.arange(n) * 1e-5,
        "device_id": "collar_01",
    })


def test_a_source_that_measures_no_speed_is_conformant():
    """A Doppler solution costs energy; many low-power receivers skip it.

    Until 1.0.0a3 the specification said this file was fine and the validator
    refused it, so the two documents this project publishes contradicted each
    other on every file of that shape.
    """
    report = tele.validate(_positions_only(), level="full")
    assert report.ok, report.errors


def test_a_source_that_does_measure_a_speed_is_still_conformant():
    df = _positions_only().assign(speed_mps=np.float32(12.0))
    assert tele.validate(df, level="full").ok
