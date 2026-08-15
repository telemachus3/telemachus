"""Trip reconstruction — pluggable, with two simple built-in strategies.

Convenience tier (SPEC-04 §5.3), and the clearest case for the tier existing at
all: cutting a continuous stream of positions into trips is not a property of
the data, it is a decision, and different decisions give different counts. Since
almost everything downstream is expressed per trip — distances, durations,
map-matching requests, invoices — that decision deserves to be explicit and
swappable rather than buried in a pipeline.

Two strategies ship with the library, deliberately simple:

``by_gap``
    Cut where the stream goes silent. Answers "when did we stop hearing from
    the device", which is a property of the transport, not of the vehicle.

``by_stop``
    Cut where the vehicle stands still long enough. Answers "when did the
    vehicle stop", which is usually what a fleet operator means by a trip.

Neither attempts to qualify a stop — to tell a delivery from a traffic light,
a driver break from a depot return. That needs more than a threshold, and it
is precisely the kind of domain logic an integrator will want to bring. Any
callable matching :class:`TripSegmenter` can be passed to
:func:`segment_trips`, so a proprietary segmenter drops in without forking:

    def my_segmenter(df, *, by, ts):
        ...                     # returns one trip index per row
        return trip_ids

    trips = segment_trips(df, strategy=my_segmenter)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
import pandas as pd

from ..metrics.basic import haversine_m
from ..metrics.sampling import gaps

__all__ = [
    "TripSegmenter",
    "by_gap",
    "by_stop",
    "segment_trips",
    "trip_profile",
]


@runtime_checkable
class TripSegmenter(Protocol):
    """Assigns a trip index to every row of a frame.

    Implementations must return a Series aligned on the input frame's index,
    numbering restarting at 0 for each entity. They must not reorder or drop
    rows: callers rely on being able to attach the result back to the frame.
    """

    def __call__(self, df: pd.DataFrame, *, by: str, ts: str) -> pd.Series:
        ...


def _number_from_breaks(base: pd.DataFrame, is_break: pd.Series, by: str,
                        original_index: pd.Index) -> pd.Series:
    """Turn a boolean break marker into 0-based trip indices per entity."""
    entity = base.loc[is_break.index, by]
    trip = is_break.groupby(entity, sort=False).cumsum() - 1
    return trip.reindex(base.index).astype("int64").set_axis(original_index)


def by_gap(max_gap_s: float = 900.0) -> TripSegmenter:
    """Cut the stream wherever it goes silent for longer than ``max_gap_s``.

    Beware of what this measures: a silence can be a parked vehicle, but also a
    tunnel, a dead spot, a flat battery or a transport failure. Where the feed
    carries a device-state or event channel, prefer it to a bare threshold.
    """

    def _segmenter(df: pd.DataFrame, *, by: str = "device_id",
                   ts: str = "ts") -> pd.Series:
        base = df.reset_index(drop=True)
        g = gaps(base, by, ts)
        return _number_from_breaks(base, g.isna() | (g > max_gap_s), by, df.index)

    return _segmenter


def by_stop(min_stop_s: float = 300.0, speed: str = "speed_mps") -> TripSegmenter:
    """Cut wherever the vehicle stands still for at least ``min_stop_s``.

    Closer to what an operator calls a trip than :func:`by_gap`, and far more
    sensitive to sampling cadence: a stop shorter than the sampling interval
    cannot be seen at all, so the trip count rises with the cadence. Measure
    that sensitivity — with :func:`~telemachus.analysis.stops` at several
    cadences — before pricing anything per trip.
    """

    def _segmenter(df: pd.DataFrame, *, by: str = "device_id",
                   ts: str = "ts") -> pd.Series:
        base = df.reset_index(drop=True)
        ordered = base.sort_values([by, ts])
        still = ordered[speed] == 0
        run = (~still).groupby(ordered[by], sort=False).cumsum()
        # duration of the still run each sample belongs to
        run_time = ordered.groupby([ordered[by], run])[ts].transform(
            lambda x: (x.max() - x.min()).total_seconds())
        long_stop = still & (run_time >= min_stop_s)
        # a trip starts when a long stop ends, and at each entity's first sample
        starts = long_stop.shift(fill_value=False) & ~long_stop
        first = ~ordered[by].duplicated()
        return _number_from_breaks(base, (starts | first).reindex(ordered.index),
                                   by, df.index)

    return _segmenter


def segment_trips(df: pd.DataFrame, by: str = "device_id", ts: str = "ts",
                  strategy: TripSegmenter | None = None,
                  max_gap_s: float = 900.0) -> pd.Series:
    """Assign a trip index to each sample.

    Parameters
    ----------
    strategy : TripSegmenter or None
        Segmentation strategy. ``None`` uses :func:`by_gap` with ``max_gap_s``,
        which is the cheapest defensible default, not the best one.

    Returns
    -------
    pd.Series
        Trip index per row, aligned on the input frame's index.
    """
    segmenter = strategy if strategy is not None else by_gap(max_gap_s)
    return segmenter(df, by=by, ts=ts)


def trip_profile(df: pd.DataFrame, trips: pd.Series | None = None,
                 by: str = "device_id", ts: str = "ts", lat: str = "lat",
                 lon: str = "lon", speed: str = "speed_mps",
                 strategy: TripSegmenter | None = None) -> pd.DataFrame:
    """Per-trip shape: samples, duration, distance, share spent standing still.

    The stationary share is worth reading before sizing any per-trip
    processing: a segment on which the vehicle never moves reduces to a single
    point, and costs nothing to reconstruct.

    Returns
    -------
    pd.DataFrame
        One row per trip: ``<by>``, ``trip``, ``n``, ``t0``, ``t1``,
        ``duration_s``, ``distance_km``, ``stationary_pct``.
    """
    if trips is None:
        trips = segment_trips(df, by=by, ts=ts, strategy=strategy)
    work = df.assign(_trip=trips)

    agg = (work.groupby([by, "_trip"])[ts]
               .agg(n="size", t0="min", t1="max").reset_index())
    agg["duration_s"] = (agg["t1"] - agg["t0"]).dt.total_seconds()

    ordered = work.sort_values([by, "_trip", ts])
    grp = ordered.groupby([by, "_trip"], sort=False)
    step = np.asarray(haversine_m(grp[lat].shift(), grp[lon].shift(),
                                  ordered[lat], ordered[lon]), dtype=float)
    ordered = ordered.assign(_step=np.nan_to_num(step))
    dist = (ordered.groupby([by, "_trip"])["_step"].sum() / 1000.0
            ).round(3).rename("distance_km").reset_index()
    agg = agg.merge(dist, on=[by, "_trip"], how="left")

    if speed in work.columns:
        still = (ordered.assign(_still=(ordered[speed] == 0))
                        .groupby([by, "_trip"])["_still"].mean()
                        .mul(100).round(1).rename("stationary_pct").reset_index())
        agg = agg.merge(still, on=[by, "_trip"], how="left")
    else:
        agg["stationary_pct"] = np.nan

    return (agg.rename(columns={"_trip": "trip"})
               .sort_values([by, "t0"]).reset_index(drop=True))
