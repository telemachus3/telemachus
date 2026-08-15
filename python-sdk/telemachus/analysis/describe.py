"""One-call characterisation of a telematics stream.

Answering "what is this feed?" — how many devices, over what period, at what
cadence, how much of it is a vehicle standing still, where on Earth — normally
costs a dozen ad-hoc queries, and the answers end up scattered across a
notebook rather than in the record. :func:`stream_summary` produces them
together, from a Telemachus-conformant frame.

It is deliberately descriptive: no threshold here changes a result downstream,
so it is safe to run first on an unfamiliar dataset.

Convenience tier (SPEC-04 §5.3). Several of its fields would fill a manifest
block on their own, but ``n_trips`` cannot be produced without segmenting, and
a function that cannot be used without making a decision belongs on the
decision side of the line. The individual measurements it aggregates —
:func:`~telemachus.metrics.gap_profile`, :func:`~telemachus.metrics.path_length_m` —
are normative and importable directly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..metrics.sampling import gap_profile, gaps, path_length_m
from .trips import segment_trips

__all__ = ["stream_summary"]


def _q(s: pd.Series, q: float) -> float:
    return float(s.quantile(q)) if len(s) else float("nan")


def stream_summary(df: pd.DataFrame, by: str = "device_id", ts: str = "ts",
                   lat: str = "lat", lon: str = "lon",
                   speed: str = "speed_mps",
                   trip_gap_s: float = 900.0) -> pd.Series:
    """Describe a stream: volume, coverage, cadence, motion, quality, extent.

    Parameters
    ----------
    df : pd.DataFrame
        Telemachus-conformant frame.
    by : str
        Entity column, typically ``device_id``.
    trip_gap_s : float
        Gap above which the stream is considered to have broken between two
        trips. Reported alongside the trip count, because the count means
        nothing without it.

    Returns
    -------
    pd.Series
        Named fields, ordered for reading. Absent measurements are ``NaN``
        rather than omitted, so summaries of different streams stay comparable.
    """
    out: dict[str, object] = {}

    out["n_records"] = int(len(df))
    out["n_devices"] = int(df[by].nunique()) if by in df else np.nan

    if ts in df and len(df):
        t = pd.to_datetime(df[ts])
        out["t_start"] = t.min()
        out["t_end"] = t.max()
        out["span_hours"] = round((t.max() - t.min()).total_seconds() / 3600.0, 2)
    else:
        out["t_start"] = out["t_end"] = pd.NaT
        out["span_hours"] = np.nan

    # --- cadence -----------------------------------------------------------
    if ts in df and by in df and len(df) > 1:
        prof = gap_profile(df, by=by, ts=ts)
        g = gaps(df, by=by, ts=ts).dropna()
        if len(prof):
            out["cadence_dominant_s"] = float(prof.loc[0, "gap_s"])
            out["cadence_dominant_pct"] = float(prof.loc[0, "pct"])
        else:
            out["cadence_dominant_s"] = out["cadence_dominant_pct"] = np.nan
        out["gap_p50_s"] = _q(g, 0.50)
        out["gap_p95_s"] = _q(g, 0.95)
        out["n_trips"] = int(
            df.assign(_t=segment_trips(df, by=by, ts=ts, max_gap_s=trip_gap_s))
              .groupby(by)["_t"].nunique().sum()
        )
        out["trip_gap_s"] = float(trip_gap_s)
    else:
        for k in ("cadence_dominant_s", "cadence_dominant_pct", "gap_p50_s",
                  "gap_p95_s", "n_trips", "trip_gap_s"):
            out[k] = np.nan

    # --- motion ------------------------------------------------------------
    if speed in df and df[speed].notna().any():
        s = df[speed].dropna()
        out["stationary_pct"] = round(100.0 * float((s == 0).mean()), 1)
        out["speed_p50_mps"] = _q(s[s > 0], 0.50)
        out["speed_p95_mps"] = _q(s[s > 0], 0.95)
    else:
        out["stationary_pct"] = out["speed_p50_mps"] = out["speed_p95_mps"] = np.nan

    # --- travelled distance ------------------------------------------------
    if {lat, lon, ts, by} <= set(df.columns) and len(df) > 1:
        out["distance_km"] = round(
            path_length_m(df, by=by, ts=ts, lat=lat, lon=lon,
                          max_gap_s=trip_gap_s) / 1000.0, 1)
    else:
        out["distance_km"] = np.nan

    # --- geographic extent -------------------------------------------------
    if lat in df and lon in df and df[lat].notna().any():
        valid = df[df[lat].notna() & df[lon].notna()]
        out["lat_min"], out["lat_max"] = round(float(valid[lat].min()), 4), round(float(valid[lat].max()), 4)
        out["lon_min"], out["lon_max"] = round(float(valid[lon].min()), 4), round(float(valid[lon].max()), 4)
    else:
        out["lat_min"] = out["lat_max"] = out["lon_min"] = out["lon_max"] = np.nan

    # --- positioning quality ----------------------------------------------
    for col, name in (("hdop", "hdop_p50"), ("h_accuracy_m", "h_accuracy_p50_m"),
                      ("n_satellites", "n_satellites_p50")):
        out[name] = _q(df[col].dropna().astype("float64"), 0.50) \
            if col in df and df[col].notna().any() else np.nan
    out["gnss_valid_pct"] = round(100.0 * float(df["gnss_valid"].dropna().mean()), 1) \
        if "gnss_valid" in df and df["gnss_valid"].notna().any() else np.nan

    return pd.Series(out, name="stream_summary")
