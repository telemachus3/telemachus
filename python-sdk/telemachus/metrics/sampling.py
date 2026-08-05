"""Sampling-cadence metrics.

A telematics stream is rarely sampled at the rate its documentation claims, and
what a downstream consumer receives is often a decimated view of what the device
actually acquired. These functions measure that: the cadence really present in a
stream, what decimation costs in observed distance and detected stops, and
whether a packetised feed is continuous or only covers isolated windows.

All functions take a Telemachus-conformant DataFrame — ``ts``, ``lat``, ``lon``,
``speed_mps`` — grouped by an entity column (``device_id`` by default).
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from .basic import haversine_m

__all__ = [
    "epoch_s",
    "gaps",
    "gap_profile",
    "sampling_populations",
    "path_length_m",
    "decimation_loss",
    "stops",
    "session_contiguity",
    "session_profile",
]


def epoch_s(ts: pd.Series) -> pd.Series:
    """Seconds since the Unix epoch, whatever the source resolution.

    Timestamp resolution depends on what produced the frame: pandas yields
    ``datetime64[ns]``, several query engines yield ``[us]`` or ``[s]``.
    Dividing a raw int64 view by a hard-coded constant silently produces wrong
    epochs — and therefore a decimation that keeps almost nothing — so the cast
    is always explicit.

    Telemachus timestamps are timezone-aware by specification, but frames
    rebuilt from a query engine often are not; both are accepted.
    """
    s = pd.Series(ts)
    if isinstance(s.dtype, pd.DatetimeTZDtype):
        s = s.dt.tz_convert("UTC").dt.tz_localize(None)
    return s.astype("datetime64[s]").astype("int64")


def gaps(df: pd.DataFrame, by: str | Sequence[str] = "device_id",
         ts: str = "ts") -> pd.Series:
    """Seconds elapsed between consecutive samples of the same entity."""
    keys = [by] if isinstance(by, str) else list(by)
    ordered = df.sort_values([*keys, ts])
    return ordered.groupby(keys, sort=False)[ts].diff().dt.total_seconds()


def gap_profile(df: pd.DataFrame, by: str | Sequence[str] = "device_id",
                ts: str = "ts", max_s: float | None = None) -> pd.DataFrame:
    """Distribution of sampling gaps, most frequent first.

    This is the reference measurement of a cadence, and it counts **gaps**, not
    entities — see :func:`sampling_populations` for why that distinction
    matters.

    Returns
    -------
    pd.DataFrame
        Columns ``gap_s``, ``n``, ``pct``.
    """
    g = gaps(df, by, ts).dropna()
    if max_s is not None:
        g = g[g <= max_s]
    out = g.value_counts().rename_axis("gap_s").reset_index(name="n")
    total = out["n"].sum()
    out["pct"] = (100.0 * out["n"] / total).round(2) if total else 0.0
    return out


def sampling_populations(df: pd.DataFrame, by: str = "device_id", ts: str = "ts",
                         min_gaps: int = 10, tol: float = 0.05) -> pd.DataFrame:
    """Dominant cadence per entity, with a statistical guard.

    Assigning a cadence to an entity only means something once that entity has
    been observed enough times. Without the guard, an entity seen twice yields a
    single gap that the mode promotes to a "cadence", and whole populations
    appear that do not exist — an artefact that grows as the observation window
    shrinks. Entities below ``min_gaps`` are returned with ``enough=False``
    rather than silently dropped, so the caller decides what to do with them.

    Returns
    -------
    pd.DataFrame
        Columns ``<by>``, ``n_gaps``, ``dominant`` (seconds), ``enough``,
        ``share`` (fraction of that entity's gaps within ``tol`` of dominant).
    """
    # `gaps` returns a series carrying the frame's index labels but in sorted
    # order. Pairing it with the entity column positionally would attribute a
    # gap to the wrong entity, so alignment is done on the index — over a copy
    # with a guaranteed-unique one.
    base = df.reset_index(drop=True)
    g = gaps(base, by, ts).rename("gap_s")
    d = pd.DataFrame({by: base[by], "gap_s": g}).dropna(subset=["gap_s"])

    if d.empty:
        return pd.DataFrame(columns=[by, "n_gaps", "dominant", "enough", "share"])

    def _dominant(x: pd.Series) -> float:
        modes = x.round(0).mode()
        return float(modes.iloc[0]) if len(modes) else np.nan

    res = d.groupby(by)["gap_s"].agg(n_gaps="size", dominant=_dominant).reset_index()
    res["enough"] = res["n_gaps"] >= min_gaps

    merged = d.merge(res[[by, "dominant"]], on=by)
    close = (merged["gap_s"] - merged["dominant"]).abs() <= merged["dominant"] * tol
    share = close.groupby(merged[by]).mean().rename("share")
    return res.merge(share, on=by, how="left")


def path_length_m(df: pd.DataFrame, by: str | Sequence[str] = "device_id",
                  ts: str = "ts", lat: str = "lat", lon: str = "lon",
                  max_gap_s: float | None = None) -> float:
    """Cumulative travelled distance, in metres.

    ``max_gap_s`` discards jumps: beyond that threshold two consecutive samples
    no longer describe an observed movement but a chord across a hole in the
    trace, which would inflate the total.
    """
    keys = [by] if isinstance(by, str) else list(by)
    ordered = df.sort_values([*keys, ts])
    grp = ordered.groupby(keys, sort=False)
    d = np.asarray(haversine_m(grp[lat].shift(), grp[lon].shift(),
                               ordered[lat], ordered[lon]), dtype=float)
    keep = ~np.isnan(d)
    if max_gap_s is not None:
        dt = grp[ts].diff().dt.total_seconds().to_numpy()
        keep &= dt <= max_gap_s
    return float(np.nansum(np.where(keep, d, 0.0)))


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
