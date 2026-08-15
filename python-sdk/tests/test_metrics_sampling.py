"""Tests for telemachus.metrics.sampling."""

import numpy as np
import pandas as pd
import pytest

from telemachus.analysis import decimation_loss, session_contiguity, stops
from telemachus.metrics import (
    epoch_s,
    gap_profile,
    gaps,
    path_length_m,
    sampling_populations,
)


def _track(n=600, step_s=1, lat0=48.0, lon0=2.0, dlat=1e-4,
           device="dev1", start="2026-01-01T00:00:00Z"):
    """Straight track at a constant cadence, one point every ``step_s``."""
    ts = pd.date_range(start, periods=n, freq=f"{step_s}s", tz="UTC")
    return pd.DataFrame({
        "ts": ts,
        "lat": lat0 + dlat * np.arange(n),
        "lon": np.full(n, lon0),
        "speed_mps": np.full(n, 10.0),
        "device_id": device,
    })


# --- epoch_s ---------------------------------------------------------------

@pytest.mark.parametrize("unit", ["ns", "us", "s"])
def test_epoch_s_is_resolution_independent(unit):
    """The whole decimation machinery breaks if this is resolution-dependent."""
    ts = pd.Series(pd.to_datetime(["2026-01-01T00:00:00Z",
                                   "2026-01-01T00:00:01Z"])).dt.tz_convert("UTC")
    converted = ts.astype(f"datetime64[{unit}, UTC]")
    assert epoch_s(converted).tolist() == [1767225600, 1767225601]


# --- gaps / gap_profile ----------------------------------------------------

def test_gap_profile_counts_gaps_not_rows():
    df = _track(n=10, step_s=2)
    prof = gap_profile(df)
    assert prof.loc[0, "gap_s"] == 2.0
    assert prof.loc[0, "n"] == 9          # 10 samples -> 9 gaps
    assert prof.loc[0, "pct"] == 100.0


def test_gaps_do_not_cross_entities():
    a = _track(n=5, device="a")
    b = _track(n=5, device="b", start="2026-06-01T00:00:00Z")
    g = gaps(pd.concat([a, b], ignore_index=True)).dropna()
    assert len(g) == 8                    # 4 per device, no gap across the join
    assert set(g.unique()) == {1.0}


# --- sampling_populations --------------------------------------------------

def test_sampling_populations_flags_undersampled_entities():
    """An entity seen twice must not be credited with a cadence.

    This is the guard against inventing populations on short observation
    windows: one gap is one observation, not a rate.
    """
    rich = _track(n=50, step_s=2, device="rich")
    poor = pd.DataFrame({
        "ts": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T00:15:00Z"]),
        "lat": [48.0, 48.1], "lon": [2.0, 2.0],
        "speed_mps": [0.0, 0.0], "device_id": "poor",
    })
    res = sampling_populations(pd.concat([rich, poor], ignore_index=True),
                               min_gaps=10).set_index("device_id")
    assert bool(res.loc["rich", "enough"]) is True
    assert res.loc["rich", "dominant"] == 2.0
    # the poor device does get a "dominant" value, but it is explicitly untrusted
    assert bool(res.loc["poor", "enough"]) is False
    assert res.loc["poor", "n_gaps"] == 1


# --- path_length_m ---------------------------------------------------------

def test_path_length_matches_analytic_distance():
    df = _track(n=11, dlat=1e-3)          # 10 steps of 1e-3 degree of latitude
    # one degree of latitude ~ 111.19 km on a sphere of radius 6371 km
    expected = 10 * 1e-3 * (np.pi / 180.0) * 6_371_000.0
    assert path_length_m(df) == pytest.approx(expected, rel=1e-6)


def test_path_length_max_gap_excludes_jumps():
    df = _track(n=5, dlat=1e-3)
    far = df.iloc[[4]].copy()
    far["ts"] = far["ts"] + pd.Timedelta(hours=3)
    far["lat"] = 60.0                      # teleport
    joined = pd.concat([df, far], ignore_index=True)
    assert path_length_m(joined, max_gap_s=10) == pytest.approx(path_length_m(df))


# --- decimation_loss -------------------------------------------------------

def test_decimation_loss_is_zero_on_a_straight_line():
    """Straight-line motion loses nothing to down-sampling — only turns do."""
    df = _track(n=601, step_s=1, dlat=1e-5)
    res = decimation_loss(df, [1, 10, 60]).set_index("step_s")
    assert res.loc[1, "loss_pct"] == 0.0
    assert res.loc[10, "loss_pct"] == pytest.approx(0.0, abs=0.01)
    assert res.loc[60, "loss_pct"] == pytest.approx(0.0, abs=0.01)


def test_decimation_loss_grows_monotonically_on_a_zigzag():
    """Cutting corners is exactly what coarse sampling does."""
    n = 601
    ts = pd.date_range("2026-01-01T00:00:00Z", periods=n, freq="1s", tz="UTC")
    zig = np.where(np.arange(n) % 2 == 0, 0.0, 1e-4)
    df = pd.DataFrame({"ts": ts, "lat": 48.0 + np.arange(n) * 1e-5,
                       "lon": 2.0 + zig, "speed_mps": 10.0, "device_id": "z"})
    res = decimation_loss(df, [1, 2, 10, 60]).set_index("step_s")
    losses = [res.loc[s, "loss_pct"] for s in (1, 2, 10, 60)]
    assert losses[0] == 0.0
    assert all(a <= b + 1e-9 for a, b in zip(losses, losses[1:], strict=False)), losses
    assert losses[-1] > 50.0


# --- stops -----------------------------------------------------------------

def test_stops_respects_minimum_duration():
    ts = pd.date_range("2026-01-01T00:00:00Z", periods=300, freq="1s", tz="UTC")
    speed = np.full(300, 10.0)
    speed[10:40] = 0.0                     # 29 s -> below threshold
    speed[100:250] = 0.0                   # 149 s -> counted
    df = pd.DataFrame({"ts": ts, "lat": 48.0, "lon": 2.0,
                       "speed_mps": speed, "device_id": "d"})
    found = stops(df, min_duration_s=60)
    assert len(found) == 1
    assert found.loc[0, "duration_s"] == pytest.approx(149.0)


def test_stops_vanish_when_the_stream_is_decimated():
    """The headline effect: coarse sampling hides short stops entirely."""
    ts = pd.date_range("2026-01-01T00:00:00Z", periods=1200, freq="1s", tz="UTC")
    speed = np.full(1200, 10.0)
    for start in range(0, 1200, 200):      # six stops of 90 s each
        speed[start:start + 90] = 0.0
    df = pd.DataFrame({"ts": ts, "lat": 48.0, "lon": 2.0,
                       "speed_mps": speed, "device_id": "d"})
    dense = len(stops(df, min_duration_s=60))
    epoch = epoch_s(df["ts"])
    coarse = len(stops(df[(epoch % 120) == 0], min_duration_s=60))
    assert dense == 6
    assert coarse < dense


def test_stops_empty_frame_returns_empty():
    df = _track(n=10)                      # never stops
    assert stops(df).empty


# --- session_contiguity ----------------------------------------------------

def test_session_contiguity_detects_a_continuous_feed():
    parts = []
    for i in range(4):                     # packets that abut exactly
        p = _track(n=60, start=f"2026-01-01T00:{i:02d}:00Z")
        p["packet"] = f"p{i}"
        parts.append(p)
    res = session_contiguity(pd.concat(parts, ignore_index=True), session="packet")
    assert res.loc[0, "n_transitions"] == 3
    assert res.loc[0, "contiguous_pct"] == 100.0


def test_session_contiguity_detects_holes():
    a = _track(n=60, start="2026-01-01T00:00:00Z")
    a["packet"] = "a"
    b = _track(n=60, start="2026-01-01T02:00:00Z")
    b["packet"] = "b"
    res = session_contiguity(pd.concat([a, b], ignore_index=True), session="packet")
    assert res.loc[0, "contiguous"] == 0
    assert res.loc[0, "median_gap_s"] > 3000
