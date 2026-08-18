"""Tests for telemachus.metrics.sampling."""

import numpy as np
import pandas as pd
import pytest

from telemachus.analysis import (decimation_loss, phase_profile,
                                 session_contiguity, stops)
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


def _irregular_zigzag(n=300):
    """A zigzag whose cadence varies, which is the normal shape of real feeds."""
    pattern = np.array([1, 1, 3, 1, 7, 2, 1, 1, 4, 1])
    gaps_s = np.tile(pattern, n // len(pattern) + 1)[:n - 1]
    ts = (pd.Timestamp("2026-01-01T00:00:00Z")
          + pd.to_timedelta(np.concatenate([[0], gaps_s.cumsum()]), unit="s"))
    zig = np.where(np.arange(n) % 2 == 0, 0.0, 1e-4)
    return pd.DataFrame({"ts": ts, "lat": 48.0 + np.arange(n) * 1e-5,
                         "lon": 2.0 + zig, "speed_mps": 10.0, "device_id": "z"})


def test_decimation_loss_is_never_negative_on_a_varying_cadence():
    """Down-sampling cannot lengthen a path: it replaces two sides with one.

    The defect this pins used a per-step contiguity filter (`dt == step`),
    which selected a different subset of the trace for each step, so the steps
    did not measure the same ground and their totals were not comparable.
    Measured on the public OSM traces over Rouen, whose dominant cadence covers
    only 62 % of samples: decimating to 2 s reported 840 km against 764 km
    native, a loss of -9.9 %.
    """
    res = decimation_loss(_irregular_zigzag(), [1, 2, 5, 10, 30, 60])
    assert (res["loss_pct"] >= 0).all(), res
    native = res.loc[res["step_s"].idxmin(), "km"]
    assert (res["km"] <= native + 1e-9).all(), res


def test_decimation_loss_at_the_native_step_is_the_path_length():
    """Two functions, one distance. They disagreed by a factor of 3.7."""
    df = _irregular_zigzag()
    res = decimation_loss(df, [1]).set_index("step_s")
    # `km` is rounded to the metre for reading, hence the tolerance.
    assert res.loc[1, "km"] == pytest.approx(path_length_m(df) / 1000.0, abs=1e-3)


def test_decimation_loss_does_not_cross_a_hole():
    """A chord over a gap is not travelled distance, at any step."""
    df = _track(n=100, step_s=1, dlat=1e-5)
    far = _track(n=100, step_s=1, dlat=1e-5, start="2026-01-01T05:00:00Z")
    far["lat"] += 5.0                                   # elsewhere entirely
    joined = pd.concat([df, far], ignore_index=True)
    res = decimation_loss(joined, [1, 30], max_gap_s=10).set_index("step_s")
    expected = 2 * path_length_m(df) / 1000.0
    assert res.loc[1, "km"] == pytest.approx(expected, abs=1e-3)
    # Without the guard the teleport enters as a chord and dwarfs the track.
    open_res = decimation_loss(joined, [1]).set_index("step_s")
    assert open_res.loc[1, "km"] > 100 * expected


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


# --- phase_profile ---------------------------------------------------------

def _at_phases(phases, period_s=120, cycles=50):
    """One sample per cycle, at fixed offsets inside the cycle."""
    base = pd.Timestamp("2026-01-01T00:00:00Z")
    ts = [base + pd.Timedelta(seconds=c * period_s + p)
          for c in range(cycles) for p in phases]
    return pd.DataFrame({"ts": pd.DatetimeIndex(ts), "device_id": "dev1"})


def test_phase_profile_finds_a_shared_clock():
    """Every sample on the multiple of the period lands in the first bin."""
    out = phase_profile(_at_phases([0]), 120, bins=60)
    assert out.loc[0, "share_pct"] == pytest.approx(100.0)
    assert out.loc[1:, "n"].sum() == 0


def test_phase_profile_flat_under_an_interval_rule():
    """Spread phases stay near the uniform share, which the frame carries."""
    out = phase_profile(_at_phases(range(0, 120, 2)), 120, bins=60)
    assert out["share_pct"].max() == pytest.approx(out["expected_pct"].iloc[0])


def test_phase_profile_counts_every_sample_once():
    df = _at_phases([0, 37, 119], cycles=10)
    out = phase_profile(df, 120, bins=60)
    assert out["n"].sum() == len(df)
    assert out["share_pct"].sum() == pytest.approx(100.0)


def test_phase_profile_rejects_a_zero_period():
    with pytest.raises(ValueError):
        phase_profile(_at_phases([0]), 0)


def test_phase_profile_on_an_empty_frame():
    out = phase_profile(pd.DataFrame(columns=["ts", "device_id"]), 120)
    assert out.empty
    assert list(out.columns) == ["phase_s", "n", "share_pct", "expected_pct"]
