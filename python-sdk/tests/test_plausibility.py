"""Unit plausibility — the check that catches what every schema check passes."""

import numpy as np
import pandas as pd
import pytest

import telemachus as tele
from telemachus.core.plausibility import check_units
from telemachus.core.units import G0


def _drive(n=300, speed_mps=20.0, independent=True, seed=0):
    """A straight eastbound run at roughly constant speed, 1 Hz.

    ``speed_mps`` carries a few percent of scatter around the speed the
    positions imply, because that is what an *independent* measurement looks
    like: a Doppler reading disagrees with its own positions sample by sample.
    A fixture without that scatter is indistinguishable from a column derived
    from the positions, and every cross-check written against it would be
    validating itself. ``independent=False`` builds that degenerate case on
    purpose.
    """
    lat = 49.33
    step_deg = speed_mps / (111_320 * np.cos(np.radians(lat)))
    declared = np.full(n, speed_mps, dtype=float)
    if independent:
        declared *= np.random.default_rng(seed).normal(1.0, 0.05, n)
    return pd.DataFrame({
        "ts": pd.date_range("2026-03-01T08:00:00Z", periods=n, freq="1s"),
        "lat": lat, "lon": 1.38 + np.arange(n) * step_deg,
        "speed_mps": declared, "device_id": "d1",
    })


def _errors(df, **kw):
    return [f for f in check_units(df, **kw) if f.severity == "error"]


def test_a_correct_frame_is_silent():
    assert check_units(_drive()) == []


def test_speed_in_kmh_is_caught_by_its_own_positions():
    df = _drive()
    df["speed_mps"] = df["speed_mps"] * 3.6
    errors = _errors(df)
    assert len(errors) == 1
    assert "km/h" in errors[0].message


@pytest.mark.parametrize("factor,unit", [(1.94384, "knots"), (2.23694, "mph")])
def test_other_speed_units_are_named(factor, unit):
    df = _drive(speed_mps=15.0)
    df["speed_mps"] = df["speed_mps"] * factor
    assert unit in _errors(df)[0].message


def test_a_speed_derived_from_the_positions_is_flagged_as_unverifiable():
    """The cross-check must not report a pass it has no grounds to give.

    A column derived from the positions it is about to be compared against
    agrees with them exactly. The ratio is 1, the report would be empty, and
    the silence reads as "checked".
    """
    df = _drive(independent=False)
    findings = check_units(df)
    assert findings, "a derived column must not pass silently"
    assert findings[0].severity == "warning"
    assert "cannot validate it" in findings[0].message


@pytest.mark.parametrize("factor,unit", [(3.6, "km/h"), (1.94384, "knots")])
def test_a_wrong_unit_is_still_named_on_a_derived_column(factor, unit):
    """Provenance does not excuse a unit: derived and in km/h is still km/h."""
    df = _drive(independent=False)
    df["speed_mps"] = df["speed_mps"] * factor
    assert unit in _errors(df)[0].message


def test_the_bound_alone_would_miss_a_slow_kmh_column():
    """90 km/h read as 90 m/s stays under the physics bound; the ratio does not."""
    df = _drive(speed_mps=25.0)          # 90 km/h
    df["speed_mps"] = 90.0
    assert _errors(df), "a magnitude check alone cannot see this"


def _with_accel(df, norm):
    df = df.copy()
    df["ax_mps2"] = 0.0
    df["ay_mps2"] = 0.0
    df["az_mps2"] = norm
    return df


def test_accelerometer_left_in_g_is_caught_when_the_frame_is_declared():
    df = _with_accel(_drive(), 1.0)
    errors = _errors(df, acc_frame="raw")
    assert errors and "still be in g" in errors[0].message


def test_a_raw_accelerometer_passes_when_declared_raw():
    assert _errors(_with_accel(_drive(), G0), acc_frame="raw") == []


def test_a_compensated_accelerometer_passes_when_declared_compensated():
    assert _errors(_with_accel(_drive(), 0.2), acc_frame="compensated") == []


def test_gravity_present_in_a_compensated_frame_is_an_error():
    errors = _errors(_with_accel(_drive(), G0), acc_frame="compensated")
    assert errors and "gravity is still present" in errors[0].message


def test_without_a_declared_frame_the_check_refuses_to_guess():
    """|a| ~ 1 is both a raw signal in g and a correct compensated one."""
    findings = check_units(_with_accel(_drive(), 1.0), acc_frame=None)
    assert all(f.severity == "warning" for f in findings)
    assert any("Declare the AccPeriod frame" in f.message for f in findings)


def test_gyroscope_in_degrees_per_second():
    df = _drive()
    rng = np.random.default_rng(0)
    for c in ("gx_rad_s", "gy_rad_s", "gz_rad_s"):
        df[c] = rng.normal(0, 30.0, len(df))       # deg/s magnitudes
    assert "deg/s" in _errors(df)[0].message


def test_magnetometer_in_nanotesla():
    df = _drive()
    for c, v in (("mx_uT", 20_000.0), ("my_uT", 30_000.0), ("mz_uT", 40_000.0)):
        df[c] = v
    assert "nT" in _errors(df)[0].message


def test_altitude_in_feet():
    df = _drive()
    df["altitude_gps_m"] = 12_000.0
    assert "feet" in _errors(df)[0].message


def test_validate_surfaces_the_finding():
    df = _drive()
    df["speed_mps"] = df["speed_mps"] * 3.6
    report = tele.validate(df)
    assert not report.ok
    assert any("km/h" in e for e in report.errors)


def test_a_short_frame_says_nothing():
    """Ten rows cannot support a median; silence beats a coin toss."""
    assert check_units(_drive(n=10)) == []
