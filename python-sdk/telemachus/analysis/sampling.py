"""Cadence analysis — what a sampling choice costs, and how a feed is shaped.

Convenience tier (SPEC-04 §5.3). These read the cadence measurements of
:mod:`telemachus.metrics.sampling` and turn them into judgements: how much
travelled distance a coarser step throws away, how many stops survive it,
whether a packetised feed is continuous. Every one of them depends on a
threshold or a step the caller chooses, which is exactly why none of them fills
a manifest field.
"""

from __future__ import annotations

from typing import Iterable

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
                    lat: str = "lat", lon: str = "lon") -> pd.DataFrame:
    """Travelled distance retained after down-sampling, per time step.

    For each step, only samples whose timestamp is a multiple of that step are
    kept, then only **strictly contiguous** segments are summed — those whose
    gap equals the step exactly. A looser filter lets real holes in the trace
    enter the sum as chords, which makes the result non-monotonic and
    understates the loss at coarse steps.

    The first step in ``steps`` is the reference against which loss is computed,
    so pass the native cadence first.

    Returns
    -------
    pd.DataFrame
        Columns ``step_s``, ``km``, ``loss_pct``.
    """
    epoch = epoch_s(df[ts])
    rows: list[dict] = []
    reference: float | None = None
    for step in steps:
        sub = df[(epoch % step) == 0]
        ordered = sub.sort_values([by, ts])
        grp = ordered.groupby(by, sort=False)
        d = np.asarray(haversine_m(grp[lat].shift(), grp[lon].shift(),
                                   ordered[lat], ordered[lon]))
        dt = grp[ts].diff().dt.total_seconds().to_numpy()
        km = float(np.nansum(np.where(dt == step, d, 0.0))) / 1000.0
        if reference is None:
            reference = km
        loss = 100.0 * (1 - km / reference) if reference else 0.0
        rows.append({"step_s": step, "km": round(km, 3), "loss_pct": round(loss, 2)})
    return pd.DataFrame(rows)


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
