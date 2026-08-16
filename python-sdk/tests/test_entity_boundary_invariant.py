"""The entity-boundary invariant, checked across the whole family at once.

A function that differences two consecutive rows has to say what it does when
those two rows belong to different devices. Three occurrences of the same
defect turned up separately during 1.0 — a null key in `csv_mapping`, a
constant key in `gpx`, no key at all in `speed_from_pos` and in the speed
cross-check — which is three times too many to keep fixing one at a time.

So the test is generic. It interleaves two entities that are far apart, and
requires that each one's answer be the same as if it had been alone. A function
that silently steps from one device to the other fails here, whoever writes it
next.

The failure it catches is never loud. Consecutive rows from two vehicles are
individually valid; only the step between them is nonsense, and it produces a
plausible-looking number in a plausible-looking column.
"""

import numpy as np
import pandas as pd
import pytest

from telemachus.analysis import stops, trip_profile
from telemachus.analysis.derived import speed_from_pos
from telemachus.core.plausibility import check_units
from telemachus.metrics import gap_profile, gaps, path_length_m


def _device(name, lon0, n=200, speed=15.0, seed=0):
    """One device's track. Two of these sit forty kilometres apart, so any step
    across the boundary is unmistakable — the point is that nothing says so."""
    rng = np.random.default_rng(seed)
    lat = 49.33
    lon = lon0 + np.cumsum(rng.normal(speed, 2.0, n)) / (111_320 * np.cos(np.radians(lat)))
    return pd.DataFrame({
        "ts": pd.date_range("2026-03-01T08:00:00Z", periods=n, freq="1s"),
        "lat": lat, "lon": lon,
        "speed_mps": speed * rng.normal(1.0, 0.06, n),
        "device_id": name})


@pytest.fixture
def alone():
    return _device("d1", 1.38)


@pytest.fixture
def interleaved(alone):
    """The same device, plus a second one in the same time window. Sorting by
    time alternates the rows, which is exactly how a real multi-device export
    arrives."""
    other = _device("d2", 1.90, seed=1)
    return pd.concat([alone, other], ignore_index=True).sort_values("ts")


# ---------------------------------------------------------------------------
# The family
# ---------------------------------------------------------------------------

def test_gaps_does_not_step_between_devices(alone, interleaved):
    one = gaps(alone).dropna()
    both = gaps(interleaved).dropna()
    assert len(both) == 2 * len(one)
    assert both.max() <= one.max() * 1.5, "a gap across the boundary would dwarf the rest"


def test_gap_profile_reports_the_same_cadence(alone, interleaved):
    assert gap_profile(alone).loc[0, "gap_s"] == gap_profile(interleaved).loc[0, "gap_s"]


def test_path_length_does_not_add_the_distance_between_devices(alone, interleaved):
    one = path_length_m(alone)
    both = path_length_m(interleaved)
    # Two tracks of the same shape: twice the distance, not twice plus 400 legs
    # of forty kilometres.
    assert both == pytest.approx(2 * one, rel=0.35)


def test_speed_from_pos_stays_within_the_device(alone, interleaved):
    both = speed_from_pos(interleaved).dropna()
    assert both.max() < 100, "a step between devices reads as a supersonic vehicle"


def test_trip_profile_distance_is_per_device(alone, interleaved):
    prof = trip_profile(interleaved)
    assert set(prof["device_id"]) == {"d1", "d2"}
    assert prof["distance_km"].max() < 2 * trip_profile(alone)["distance_km"].max()


def test_stops_are_not_invented_at_the_boundary(alone, interleaved):
    assert len(stops(interleaved)) == 2 * len(stops(alone))


def test_the_speed_cross_check_does_not_raise_a_false_alarm(alone, interleaved):
    """The occurrence found by writing this file. Interleaved, the implied speed
    exploded, the median ratio collapsed to 0.00, and a checker built to catch
    wrong units reported sound data as wrong."""
    assert check_units(alone) == []
    assert check_units(interleaved) == [], "false alarm on a multi-device frame"


# ---------------------------------------------------------------------------
# The guard on the guard
# ---------------------------------------------------------------------------

def test_the_fixture_would_expose_a_function_that_ignores_the_key():
    """A test suite that cannot fail proves nothing. This models the defect —
    differencing a time-sorted frame with no grouping — and shows the fixture
    catches it."""
    both = pd.concat([_device("d1", 1.38), _device("d2", 1.90, seed=1)],
                     ignore_index=True).sort_values("ts")
    from telemachus.metrics import haversine_m

    naive = np.asarray(haversine_m(both["lat"].shift(), both["lon"].shift(),
                                   both["lat"], both["lon"]), dtype=float)
    dt = both["ts"].diff().dt.total_seconds().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        implied = naive / dt
    assert np.nanmax(implied) > 1000, (
        "the ungrouped form must produce an absurd speed, or this suite is "
        "measuring nothing")
