"""Tests for session_profile and stream_summary."""

import numpy as np
import pandas as pd
import pytest

from telemachus.metrics import session_profile, stream_summary


def _track(n=120, step_s=1, device="dev1", start="2026-01-01T00:00:00Z",
           speed=10.0, dlat=1e-4):
    ts = pd.date_range(start, periods=n, freq=f"{step_s}s", tz="UTC")
    return pd.DataFrame({
        "ts": ts,
        "lat": 48.0 + dlat * np.arange(n),
        "lon": np.full(n, 2.0),
        "speed_mps": np.full(n, speed),
        "device_id": device,
    })


# --- session_profile -------------------------------------------------------

def test_session_profile_reports_size_and_duration_per_session():
    parts = []
    for i, n in enumerate([300, 300, 120]):
        p = _track(n=n, start=f"2026-01-01T0{i}:00:00Z")
        p["packet"] = f"p{i}"
        parts.append(p)
    prof = session_profile(pd.concat(parts, ignore_index=True), session="packet")
    assert list(prof["n"]) == [300, 300, 120]
    assert list(prof["duration_s"]) == [299.0, 299.0, 119.0]
    # a 1 Hz feed capped at 300 samples: mean gap stays 1 s whatever the size
    assert prof["mean_gap_s"].round(3).tolist() == [1.0, 1.0, 1.0]


def test_session_profile_single_sample_session_has_no_gap():
    df = _track(n=1)
    df["packet"] = "solo"
    prof = session_profile(df, session="packet")
    assert prof.loc[0, "n"] == 1
    assert prof.loc[0, "duration_s"] == 0.0
    assert pd.isna(prof.loc[0, "mean_gap_s"])


# --- stream_summary --------------------------------------------------------

def test_stream_summary_reports_volume_cadence_and_extent():
    df = _track(n=600, step_s=2, dlat=1e-4)
    s = stream_summary(df)
    assert s["n_records"] == 600
    assert s["n_devices"] == 1
    assert s["cadence_dominant_s"] == 2.0
    assert s["cadence_dominant_pct"] == 100.0
    assert s["span_hours"] == round(1198 / 3600, 2)   # summary rounds to 2 dp
    assert s["lat_min"] == 48.0
    assert s["stationary_pct"] == 0.0
    assert s["distance_km"] > 0


def test_stream_summary_counts_stationary_share():
    df = _track(n=100)
    df.loc[:59, "speed_mps"] = 0.0            # 60 of 100 samples standing still
    assert stream_summary(df)["stationary_pct"] == 60.0


def test_stream_summary_missing_fields_are_nan_not_absent():
    """Summaries of different streams must stay comparable."""
    df = _track(n=50)[["ts", "lat", "lon", "device_id"]]   # no speed, no quality
    s = stream_summary(df)
    for field in ("stationary_pct", "hdop_p50", "h_accuracy_p50_m",
                  "n_satellites_p50", "gnss_valid_pct"):
        assert field in s.index
        assert pd.isna(s[field])
    assert s["n_records"] == 50               # the rest is still computed


def test_stream_summary_reports_quality_when_present():
    df = _track(n=50)
    df["hdop"] = 1.0
    df["n_satellites"] = 20
    df["gnss_valid"] = True
    s = stream_summary(df)
    assert s["hdop_p50"] == 1.0
    assert s["n_satellites_p50"] == 20.0
    assert s["gnss_valid_pct"] == 100.0


def test_stream_summary_trip_count_carries_its_threshold():
    parts = [_track(n=10, start=f"2026-01-01T00:{m:02d}:00Z") for m in (0, 30)]
    df = pd.concat(parts, ignore_index=True)
    s = stream_summary(df, trip_gap_s=900)
    assert s["n_trips"] == 2
    assert s["trip_gap_s"] == 900.0
