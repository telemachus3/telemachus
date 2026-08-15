"""Multi-rate merge (SPEC-01 §2.11), including the orphan fix."""

import numpy as np
import pandas as pd
import pytest

import telemachus as tele

T0 = pd.Timestamp("2026-03-01T08:00:00Z")


def _bursts(seconds, size=10, rate_hz=10):
    """`size` accelerometer samples per second, for each second listed."""
    frames = []
    for s in seconds:
        base = T0 + pd.Timedelta(seconds=s)
        frames.append(pd.DataFrame({
            "ts": [base + pd.Timedelta(seconds=i / rate_hz) for i in range(size)],
            "ax_mps2": 0.1, "ay_mps2": 0.0, "az_mps2": 9.8}))
    return pd.concat(frames, ignore_index=True)


def _fixes(n):
    return pd.DataFrame({
        "ts": pd.date_range(T0, periods=n, freq="1s"),
        "lat": 49.33 + np.arange(n) * 1e-4, "lon": 1.38, "speed_mps": 13.0})


def _distinct_fixes(df):
    return df.loc[df["lat"].notna(), "lat"].nunique()


def test_tolerance_has_no_default():
    """It encodes hardware knowledge; a library-wide default would be a guess."""
    with pytest.raises(TypeError):
        tele.merge_multirate(_bursts([0]), _fixes(1))


def test_dense_accelerometer_matches_a_naive_left_join():
    accel, gps = _bursts(range(6)), _fixes(6)
    merged = tele.merge_multirate(accel, gps, tolerance_ms=600)
    naive = pd.merge_asof(accel, gps, on="ts", direction="nearest",
                          tolerance=pd.Timedelta("600ms"))
    assert len(merged) == len(naive)
    assert _distinct_fixes(merged) == _distinct_fixes(naive) == 6


def test_a_fix_inside_an_accelerometer_gap_is_kept():
    """The bug this function exists to remove: the naive join loses the fix."""
    accel = _bursts([0, 1, 2, 5, 6])          # nothing between 3 s and 5 s
    gps = _fixes(7)
    naive = pd.merge_asof(accel, gps, on="ts", direction="nearest",
                          tolerance=pd.Timedelta("600ms"))
    merged = tele.merge_multirate(accel, gps, tolerance_ms=600)

    assert _distinct_fixes(naive) == 6
    assert _distinct_fixes(merged) == 7
    orphan = merged[merged["ax_mps2"].isna()]
    assert len(orphan) == 1
    assert orphan["ts"].iloc[0] == T0 + pd.Timedelta(seconds=4)


def test_the_orphan_row_carries_no_invented_accelerometer_value():
    merged = tele.merge_multirate(_bursts([0, 1, 2, 5, 6]), _fixes(7),
                                  tolerance_ms=600)
    orphan = merged[merged["lat"].notna() & merged["ax_mps2"].isna()]
    assert orphan[["ax_mps2", "ay_mps2", "az_mps2"]].isna().all(axis=None)


def test_a_day_with_no_fix_keeps_the_accelerometer():
    accel = _bursts(range(3))
    out = tele.merge_multirate(accel, _fixes(0), tolerance_ms=600)
    assert len(out) == len(accel)


def test_a_device_with_no_accelerometer_keeps_the_track():
    gps = _fixes(5)
    out = tele.merge_multirate(gps.iloc[0:0], gps, tolerance_ms=600)
    assert len(out) == 5


def test_result_is_sorted_and_indexed_from_zero():
    merged = tele.merge_multirate(_bursts([0, 1, 2, 5, 6]), _fixes(7),
                                  tolerance_ms=600)
    assert merged["ts"].is_monotonic_increasing
    assert list(merged.index) == list(range(len(merged)))


def test_mismatched_timestamp_resolutions_merge():
    """A short extract can come back as [s] where a full day gives [ns]."""
    accel = _bursts([0, 1])
    accel["ts"] = accel["ts"].astype("datetime64[s, UTC]")
    gps = _fixes(2)
    assert len(tele.merge_multirate(accel, gps, tolerance_ms=600)) == 20
