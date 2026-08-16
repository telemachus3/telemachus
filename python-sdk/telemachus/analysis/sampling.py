"""Cadence analysis — what a sampling choice costs, and how a feed is shaped.

Convenience tier (SPEC-04 §5.3). These read the cadence measurements of
:mod:`telemachus.metrics.sampling` and turn them into judgements: how much
travelled distance a coarser step throws away, how many stops survive it,
whether a packetised feed is continuous. Every one of them depends on a
threshold or a step the caller chooses, which is exactly why none of them fills
a manifest field.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from ..metrics.basic import haversine_m
from ..metrics.sampling import epoch_s

__all__ = [
    "decimation_loss",
    "stops",
    "session_contiguity",
    "session_profile",
]


def decimation_loss(df: pd.DataFrame, steps: Iterable[int],
                    by: str = "device_id", ts: str = "ts",
                    lat: str = "lat", lon: str = "lon",
                    max_gap_s: float | None = None) -> pd.DataFrame:
    """Travelled distance retained after down-sampling, per time step.

    Down-sampling a path can only shorten it: dropping a sample replaces two
    sides of a triangle with the third. So the loss is a corner-cutting
    measurement, it is bounded below by zero, and a coarser step throws away
    more of the turns.

    The reference is the **native** path, not the first step, so every row of
    the result answers the same question: what fraction of the travelled
    distance survives this cadence. Passing a step finer than the actual
    cadence therefore reports a loss near zero rather than a spurious gain.

    ``max_gap_s`` splits the trace into contiguous stretches first, so a real
    hole is never crossed by a chord. The split is computed **once, on the
    native signal**, and every step then decimates inside those same stretches.
    That is what makes the steps comparable: they measure the same ground.

    A caveat rather than a guarantee: two steps that are not multiples of one
    another sample different instants, so their losses can cross by a little on
    a feed whose cadence varies. What cannot happen is a negative loss, which
    is what a per-step contiguity filter used to produce.

    Parameters
    ----------
    steps : iterable of int
        Sampling steps in seconds, e.g. ``[1, 5, 30, 60]``. Order does not
        affect the numbers.
    max_gap_s : float or None
        Beyond this, two consecutive samples no longer describe an observed
        movement. ``None`` treats each entity as one uninterrupted stretch.

    Returns
    -------
    pd.DataFrame
        Columns ``step_s``, ``km``, ``loss_pct``, ordered by ``step_s``.
    """
    ordered = df.sort_values([by, ts]).reset_index(drop=True)
    if ordered.empty:
        return pd.DataFrame(columns=["step_s", "km", "loss_pct"])

    dt = ordered.groupby(by, sort=False)[ts].diff().dt.total_seconds()
    starts = dt.isna()
    if max_gap_s is not None:
        starts = starts | (dt > max_gap_s)
    stretch = starts.cumsum().to_numpy()

    native = _stretch_km(ordered, stretch, lat, lon)
    epoch = epoch_s(ordered[ts]).to_numpy()
    # Last sample of each stretch, always kept: decimating must not shorten the
    # path by truncating its end, which would be measured as corner-cutting.
    last = np.empty(len(stretch), dtype=bool)
    last[-1] = True
    last[:-1] = stretch[:-1] != stretch[1:]

    rows = []
    for step in sorted({int(s) for s in steps}):
        window = np.floor_divide(epoch, step)
        first = np.empty(len(window), dtype=bool)
        first[0] = True
        first[1:] = (window[1:] != window[:-1]) | (stretch[1:] != stretch[:-1])
        keep = first | last
        km = _stretch_km(ordered[keep], stretch[keep], lat, lon)
        loss = 100.0 * (1 - km / native) if native else 0.0
        rows.append({"step_s": step, "km": round(km, 3),
                     "loss_pct": round(loss, 2)})
    return pd.DataFrame(rows)


def _stretch_km(frame: pd.DataFrame, stretch: np.ndarray,
                lat: str, lon: str) -> float:
    """Path length of a frame, summed within contiguous stretches."""
    if len(frame) < 2:
        return 0.0
    same = stretch[1:] == stretch[:-1]
    d = np.asarray(haversine_m(frame[lat].to_numpy()[:-1],
                               frame[lon].to_numpy()[:-1],
                               frame[lat].to_numpy()[1:],
                               frame[lon].to_numpy()[1:]), dtype=float)
    return float(np.nansum(np.where(same, d, 0.0))) / 1000.0


def stops(df: pd.DataFrame, by: str = "device_id", ts: str = "ts",
          speed: str = "speed_mps", min_duration_s: float = 60.0) -> pd.DataFrame:
    """Stops detected as runs of zero speed lasting at least ``min_duration_s``.

    How many stops this finds depends strongly on the sampling cadence — that is
    the point of the function, not a limitation. Running it at several cadences
    measures what down-sampling destroys: short stops vanish entirely, and the
    ones that survive appear longer than they were.

    Returns
    -------
    pd.DataFrame
        One row per stop: ``<by>``, ``t0``, ``t1``, ``n``, ``duration_s``.
    """
    ordered = df.sort_values([by, ts]).copy()
    moving = (ordered[speed] != 0).astype(int)
    ordered["_run"] = moving.groupby(ordered[by], sort=False).cumsum()
    still = ordered[ordered[speed] == 0]
    if still.empty:
        return pd.DataFrame(columns=[by, "t0", "t1", "n", "duration_s"])
    agg = (still.groupby([by, "_run"])[ts]
                .agg(t0="min", t1="max", n="size").reset_index())
    agg["duration_s"] = (agg["t1"] - agg["t0"]).dt.total_seconds()
    return (agg[agg["duration_s"] >= min_duration_s]
            .drop(columns="_run").reset_index(drop=True))


def session_profile(df: pd.DataFrame, session: str, by: str = "device_id",
                    ts: str = "ts") -> pd.DataFrame:
    """Shape of each delivery unit: how many samples, over how long.

    A feed arriving in packets, bursts or files is often shaped by a transport
    constraint rather than by the phenomenon observed — a cap on samples per
    unit, or a fixed time window. Reading sample count against duration tells
    which of the two binds: a constant count with varying duration means the
    cap binds, a constant duration with varying count means the window does.

    Returns
    -------
    pd.DataFrame
        One row per session: ``<by>``, ``<session>``, ``n``, ``t0``, ``t1``,
        ``duration_s``, ``mean_gap_s``.
    """
    agg = (df.groupby([by, session])[ts]
             .agg(n="size", t0="min", t1="max").reset_index())
    agg["duration_s"] = (agg["t1"] - agg["t0"]).dt.total_seconds()
    agg["mean_gap_s"] = (agg["duration_s"] / (agg["n"] - 1)).where(agg["n"] > 1)
    return agg.sort_values([by, "t0"]).reset_index(drop=True)


def session_contiguity(df: pd.DataFrame, session: str, by: str = "device_id",
                       ts: str = "ts", tol_s: float = 1.0) -> pd.DataFrame:
    """Whether successive sessions of an entity follow one another without a hole.

    A feed delivered in packets, bursts or files may be continuous — each unit
    starting where the previous one ended — or may only cover isolated windows.
    The distinction decides whether the underlying signal can be treated as a
    continuous trajectory.

    Returns
    -------
    pd.DataFrame
        Single row: ``n_transitions``, ``contiguous``, ``contiguous_pct``,
        ``median_gap_s``.
    """
    bounds = (df.groupby([by, session])[ts].agg(t0="min", t1="max")
                .reset_index().sort_values([by, "t0"]))
    bounds["gap_s"] = (bounds["t0"] - bounds.groupby(by)["t1"].shift()).dt.total_seconds()
    g = bounds["gap_s"].dropna()
    if g.empty:
        return pd.DataFrame([{"n_transitions": 0, "contiguous": 0,
                              "contiguous_pct": float("nan"), "median_gap_s": float("nan")}])
    return pd.DataFrame([{
        "n_transitions": int(len(g)),
        "contiguous": int((g <= tol_s).sum()),
        "contiguous_pct": round(100.0 * float((g <= tol_s).mean()), 1),
        "median_gap_s": float(g.median()),
    }])
