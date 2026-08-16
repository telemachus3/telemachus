"""Tests for telemachus.analysis.derived.

Neither function had one. `speed_from_pos` shipped without a `by=` parameter,
so on a multi-entity frame it differenced across the boundary between two
devices, where time runs backwards and the speed comes out signed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from telemachus.analysis import compute_dt, speed_from_pos


def _leg(device, start, lat0=48.0, n=3):
    """Three fixes a second apart, moving north at a constant rate."""
    return pd.DataFrame({
        "ts": pd.date_range(start, periods=n, freq="1s", tz="UTC"),
        "lat": lat0 + 1e-4 * np.arange(n),
        "lon": 2.0,
        "device_id": device,
    })


@pytest.fixture
def two_devices():
    """Two entities whose periods do not overlap, second one earlier.

    The order that matters is the frame's, not the clock's: sorting by
    (device_id, ts) puts device b's first fix straight after device a's last,
    four hours earlier. That boundary is where dt goes negative.
    """
    return pd.concat([_leg("a", "2026-01-01T12:00:00Z"),
                      _leg("b", "2026-01-01T08:00:00Z", lat0=49.0)],
                     ignore_index=True)


def test_speed_is_never_signed_across_an_entity_boundary(two_devices):
    """Measured on a 120-badge export before the fix: -81 to +204 m/s."""
    v = speed_from_pos(two_devices)
    assert not (v.dropna() < 0).any(), v.tolist()


def test_every_entity_starts_with_nan_not_just_the_frame(two_devices):
    """`v[0] = nan` blanked one row; each entity needs its own."""
    v = speed_from_pos(two_devices)
    assert v.isna().sum() == 2
    assert np.isnan(v.iloc[0]) and np.isnan(v.iloc[3])


def test_speed_matches_the_analytic_value_within_an_entity(two_devices):
    """1e-4 degree of latitude per second on a sphere of radius 6371 km."""
    expected = 1e-4 * (np.pi / 180.0) * 6_371_000.0
    v = speed_from_pos(two_devices).dropna()
    assert v.to_numpy() == pytest.approx(expected, rel=1e-6)


def test_by_none_treats_the_frame_as_one_entity(two_devices):
    """The old behaviour stays reachable, and shows what it used to cost."""
    v = speed_from_pos(two_devices, by=None)
    assert v.isna().sum() == 1
    assert (v.dropna() < 0).any()          # the boundary, unguarded


def test_a_missing_entity_column_is_not_an_error():
    """A single-entity frame need not carry a device_id at all."""
    df = _leg("a", "2026-01-01T12:00:00Z").drop(columns="device_id")
    v = speed_from_pos(df)
    assert np.isnan(v.iloc[0])
    assert (v.dropna() > 0).all()


def test_alignment_survives_a_non_default_index(two_devices):
    """The result is joined back onto the caller's frame, so it must align."""
    shifted = two_devices.set_index(pd.RangeIndex(100, 106))
    v = speed_from_pos(shifted)
    assert v.index.equals(shifted.index)


def test_compute_dt_is_documented_as_entity_blind(two_devices):
    """It takes a Series, so it cannot group. The docstring must say so."""
    assert "group" in compute_dt.__doc__.lower()
    dt = compute_dt(two_devices["ts"])
    assert (dt.dropna() < 0).any()         # exactly what the docstring warns of
