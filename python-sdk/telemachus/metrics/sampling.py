"""Sampling-cadence measurement.

Normative tier (SPEC-04 §5.3). A telematics stream is rarely sampled at the rate
its documentation claims, and ``sensors.*.rate_hz`` in a SPEC-02 manifest is
defined as the *observed effective rate*, not the datasheet one. These functions
are what measures it: the distribution of gaps actually present in a stream, the
dominant cadence per device, and the travelled distance that goes into
``volume.distance_km``.

What a coarser cadence *costs* — stops missed, distance lost, delivery units
shaped by a transport constraint — is a judgement rather than a measurement, and
lives in :mod:`telemachus.analysis.sampling`.

All functions take a Telemachus-conformant DataFrame — ``ts``, ``lat``, ``lon``,
``speed_mps`` — grouped by an entity column (``device_id`` by default).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .basic import haversine_m

__all__ = [
    "epoch_s",
    "gaps",
    "gap_profile",
    "sampling_populations",
    "path_length_m",
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
