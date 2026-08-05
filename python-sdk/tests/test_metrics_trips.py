"""Tests for trip reconstruction: built-in strategies and pluggability."""

import numpy as np
import pandas as pd
import pytest

from telemachus.metrics import (
    TripSegmenter,
    by_gap,
    by_stop,
    segment_trips,
    trip_profile,
)


def _leg(n=60, start="2026-01-01T00:00:00Z", device="dev1", speed=10.0,
         lat0=48.0, dlat=1e-4):
    ts = pd.date_range(start, periods=n, freq="1s", tz="UTC")
    return pd.DataFrame({
        "ts": ts,
        "lat": lat0 + dlat * np.arange(n),
        "lon": np.full(n, 2.0),
        "speed_mps": np.full(n, float(speed)),
        "device_id": device,
    })


# --- by_gap ----------------------------------------------------------------

def test_by_gap_cuts_on_silence():
    df = pd.concat([_leg(start="2026-01-01T00:00:00Z"),
                    _leg(start="2026-01-01T02:00:00Z")], ignore_index=True)
    assert segment_trips(df, strategy=by_gap(900)).nunique() == 2


def test_by_gap_threshold_governs_the_count():
    """The trip count is a modelling choice, and the API says so."""
    parts = [_leg(n=10, start=f"2026-01-01T00:{m:02d}:00Z") for m in (0, 5, 10)]
    df = pd.concat(parts, ignore_index=True)
    assert segment_trips(df, strategy=by_gap(60)).nunique() == 3
    assert segment_trips(df, strategy=by_gap(3600)).nunique() == 1


def test_by_gap_is_the_default_strategy():
    df = pd.concat([_leg(start="2026-01-01T00:00:00Z"),
                    _leg(start="2026-01-01T02:00:00Z")], ignore_index=True)
    assert segment_trips(df).equals(segment_trips(df, strategy=by_gap(900)))


# --- by_stop ---------------------------------------------------------------

def test_by_stop_cuts_on_a_long_standstill_not_on_a_brief_one():
    moving_a = _leg(n=60, start="2026-01-01T00:00:00Z")
    brief = _leg(n=30, start="2026-01-01T00:01:00Z", speed=0)      # 30 s
    moving_b = _leg(n=60, start="2026-01-01T00:01:30Z")
    long_stop = _leg(n=600, start="2026-01-01T00:02:30Z", speed=0)  # 10 min
    moving_c = _leg(n=60, start="2026-01-01T00:12:30Z")
    df = pd.concat([moving_a, brief, moving_b, long_stop, moving_c],
                   ignore_index=True)
    trips = segment_trips(df, strategy=by_stop(min_stop_s=300))
    assert trips.nunique() == 2          # only the 10-minute stop splits


def test_by_stop_and_by_gap_disagree_on_a_parked_but_reporting_vehicle():
    """A vehicle standing still while still reporting: a stop, not a silence."""
    df = pd.concat([_leg(n=60, start="2026-01-01T00:00:00Z"),
                    _leg(n=600, start="2026-01-01T00:01:00Z", speed=0),
                    _leg(n=60, start="2026-01-01T00:11:00Z")], ignore_index=True)
    assert segment_trips(df, strategy=by_gap(900)).nunique() == 1
    assert segment_trips(df, strategy=by_stop(300)).nunique() == 2


# --- pluggability ----------------------------------------------------------

def test_a_custom_segmenter_can_be_plugged_in():
    """The point of the protocol: proprietary logic drops in without a fork."""

    def every_other_sample(df, *, by, ts):
        return pd.Series(np.arange(len(df)) // 30, index=df.index)

    assert isinstance(every_other_sample, TripSegmenter)
    df = _leg(n=90)
    assert segment_trips(df, strategy=every_other_sample).nunique() == 3


def test_builtin_strategies_satisfy_the_protocol():
    assert isinstance(by_gap(900), TripSegmenter)
    assert isinstance(by_stop(300), TripSegmenter)


# --- alignment contract ----------------------------------------------------

def test_segmenters_return_index_aligned_series_on_shuffled_input():
    df = _leg(n=40).sample(frac=1.0, random_state=0)
    for strategy in (by_gap(900), by_stop(300)):
        trips = segment_trips(df, strategy=strategy)
        assert trips.index.equals(df.index)
        assert len(trips) == len(df)


def test_numbering_restarts_per_device():
    a = pd.concat([_leg(n=30, device="a", start="2026-01-01T00:00:00Z"),
                   _leg(n=30, device="a", start="2026-01-01T03:00:00Z")])
    b = _leg(n=30, device="b")
    trips = segment_trips(pd.concat([a, b], ignore_index=True))
    df = pd.concat([a, b], ignore_index=True).assign(trip=trips)
    assert sorted(df[df.device_id == "a"].trip.unique()) == [0, 1]
    assert sorted(df[df.device_id == "b"].trip.unique()) == [0]


# --- trip_profile ----------------------------------------------------------

def test_trip_profile_reports_shape_per_trip():
    df = pd.concat([_leg(n=60, start="2026-01-01T00:00:00Z"),
                    _leg(n=120, start="2026-01-01T02:00:00Z")], ignore_index=True)
    prof = trip_profile(df)
    assert list(prof["n"]) == [60, 120]
    assert list(prof["duration_s"]) == [59.0, 119.0]
    assert (prof["distance_km"] > 0).all()
    assert list(prof["stationary_pct"]) == [0.0, 0.0]


def test_trip_profile_flags_a_segment_that_never_moves():
    """Reducible to a point — it costs nothing to reconstruct."""
    df = _leg(n=60, speed=0, dlat=0.0)
    prof = trip_profile(df)
    assert prof.loc[0, "stationary_pct"] == 100.0
    assert prof.loc[0, "distance_km"] == 0.0


def test_trip_profile_accepts_precomputed_trips():
    df = _leg(n=60)
    trips = segment_trips(df, strategy=by_stop(300))
    assert len(trip_profile(df, trips=trips)) == trips.nunique()
