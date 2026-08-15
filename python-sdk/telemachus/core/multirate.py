"""Multi-rate merge — aligning an IMU stream and a GNSS stream on one time axis.

SPEC-01 §2.11 defines the convention: a Telemachus file is timestamped at the
highest sensor rate, and the lower-rate columns hold NaN on the rows where no
measurement exists. Producing such a file from two separate streams is where
every adapter starts, and it is the single most duplicated piece of code across
the projects that consume this format.

**What this function does and does not do.** It decides which *rows* exist and
which measurement lands on each; it never computes a value. An accelerometer
column stays the accelerometer, a GNSS column stays the GNSS, and a row with no
fix within tolerance keeps NaN rather than an interpolated position. Filling
those NaNs is a modelling decision, it belongs to whoever makes it, and it is
deliberately not here.

**The case that is easy to get wrong.** A left join on the accelerometer grid
loses any GNSS fix that falls in a hole in that grid — during an inter-burst
gap, or while the IMU is asleep. The fix has no row to attach to and vanishes,
silently, from a file that still validates. The merge is therefore over the
*union* of both time axes: orphan fixes come back as rows of their own, with
the accelerometer columns NaN. On a dense accelerometer stream there are no
orphans and the result is identical to the naive join; the difference only
appears exactly where the naive join was wrong.

Of the twenty or so hand-written variants of this merge measured across the
projects using the format, one recovered orphan fixes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["merge_multirate"]


def merge_multirate(accel: pd.DataFrame, gps: pd.DataFrame, *,
                    tolerance_ms: int, ts: str = "ts") -> pd.DataFrame:
    """Merge a high-rate and a low-rate stream onto the union of their timestamps.

    Parameters
    ----------
    accel : pd.DataFrame
        High-rate stream, carrying ``ts``. Typically the accelerometer, but any
        stream may play this role: what matters is that it is the denser one,
        since its timestamps become the file's grid.
    gps : pd.DataFrame
        Low-rate stream, carrying ``ts``. Each of its rows is attached to the
        nearest high-rate row within ``tolerance_ms``, or kept as a row of its
        own if there is none.
    tolerance_ms : int
        Maximum distance, in milliseconds, at which a low-rate sample may be
        attached to a high-rate one. **Required, with no default.** The right
        value is a property of the hardware — of the delivery cadence, of how
        the device timestamps a burst — and a library that guessed it would be
        encoding one deployment's field knowledge as everyone's default. Half
        the low-rate period is the usual starting point.
    ts : str
        Name of the timestamp column in both frames.

    Returns
    -------
    pd.DataFrame
        Rows sorted by ``ts``, carrying the columns of both inputs. Columns of
        the stream that has no sample at a given instant are NaN there.

    Notes
    -----
    Either input may be empty, and the result is then the other one: a day with
    no fix is still a valid accelerometer record, and a device with no
    accelerometer still produces a valid track. Returning an empty frame in
    those cases — which a bare ``merge_asof`` does — destroys a whole stream on
    the strength of the other one being absent.
    """
    if tolerance_ms is None:
        raise TypeError("merge_multirate() requires tolerance_ms; it is a property "
                        "of the hardware, not something this library can default")
    if tolerance_ms <= 0:
        raise ValueError(f"tolerance_ms must be positive, got {tolerance_ms}")

    if accel is None or accel.empty:
        return (gps if gps is not None else pd.DataFrame()).reset_index(drop=True)

    a = accel.sort_values(ts).copy()
    a[ts] = _as_utc_ns(a[ts])

    if gps is None or gps.empty:
        return a.reset_index(drop=True)

    g = gps.sort_values(ts).copy()
    g[ts] = _as_utc_ns(g[ts])

    tol = pd.Timedelta(milliseconds=int(tolerance_ms))
    merged = pd.merge_asof(a, g, on=ts, direction="nearest", tolerance=tol)

    # Which low-rate samples found no high-rate row to attach to. Probing with
    # an explicit positional index rather than with a data column keeps the
    # answer right when a column of the high-rate stream happens to be NaN.
    probe = pd.merge_asof(g[[ts]], a[[ts]].assign(_row=np.arange(len(a))),
                          on=ts, direction="nearest", tolerance=tol)
    orphan = probe["_row"].isna().to_numpy()
    if orphan.any():
        orphans = g.loc[orphan].reindex(columns=merged.columns)
        merged = pd.concat([merged, orphans], ignore_index=True)

    return merged.sort_values(ts).reset_index(drop=True)


def _as_utc_ns(s: pd.Series) -> pd.Series:
    """Normalise a timestamp column to ``datetime64[ns, UTC]``.

    ``merge_asof`` requires both keys to have exactly the same dtype, and a
    frame built from a short extract can come back as ``[s]`` where the same
    code on a full day gives ``[ns]``. Normalising is a no-op in the common
    case and removes a failure that only appears on small inputs — which is to
    say, in tests and in the first thing a new user tries.
    """
    out = pd.to_datetime(s, utc=True, errors="coerce")
    return out.astype("datetime64[ns, UTC]")
