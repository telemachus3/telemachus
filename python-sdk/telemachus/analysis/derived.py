"""Quantities computed from the record rather than measured in it.

Convenience tier (SPEC-04 §5.3), and the tier boundary here is not a matter of
taste: SPEC-04 §5.2 says the specification describes what columns exist and what
they mean, never how to compute a derived value. A speed estimated from
consecutive positions is a derived value. It is genuinely useful — it is the
independent check that catches a ``speed_mps`` column left in km/h — but it is
one estimator among several, and it does not belong in the normative tier.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..metrics.basic import haversine_m

__all__ = ["compute_dt", "speed_from_pos"]


def compute_dt(ts: pd.Series) -> pd.Series:
    """Delta t in seconds (NaN for the first row).

    Takes a Series, so it knows nothing about entities: on a frame holding
    several devices it will difference across the boundary between two of them.
    Group before calling, or use :func:`speed_from_pos`, which does.
    """
    ts = pd.to_datetime(ts, utc=True, errors="coerce")
    return ts.diff().dt.total_seconds()


def speed_from_pos(df: pd.DataFrame, *, by: str | None = "device_id",
                   ts: str = "ts", lat: str = "lat",
                   lon: str = "lon") -> pd.Series:
    """Speed in m/s estimated from timestamp and position, by backward difference.

    Returns a Series aligned on ``df.index``, NaN on the first row of each
    entity. Straight-line distance between consecutive fixes understates a
    curve, so this reads low on winding roads and at coarse cadences — enough
    to check a unit, not enough to replace a measurement.

    Differencing consecutive rows is only meaningful within one entity. On a
    frame sorted by ``(by, ts)``, the row where one device ends and the next
    begins has a *negative* ``dt``, so the speed comes out signed: values from
    -81 to +204 m/s were measured on a 120-badge export. A threshold applied to
    a quantity assumed positive then reports either every row as a stop or none
    of them, depending on which way the comparison runs.

    Parameters
    ----------
    by : str or None
        Entity column. Rows are differenced within each entity, and the first
        row of each is NaN. ``None``, or a name the frame does not carry,
        treats the whole frame as one entity — correct only if it is.

    Notes
    -----
    Rows are differenced in the order given. A frame that is not sorted by
    ``(by, ts)`` yields distances between fixes that are not consecutive.
    """
    if by and by in df.columns:
        grouped = df.groupby(by, sort=False)
        dt = grouped[ts].diff().dt.total_seconds().to_numpy()
        prev_lat = grouped[lat].shift(1).to_numpy()
        prev_lon = grouped[lon].shift(1).to_numpy()
    else:
        dt = compute_dt(df[ts]).to_numpy()
        prev_lat = df[lat].shift(1).to_numpy()
        prev_lon = df[lon].shift(1).to_numpy()

    dist = haversine_m(prev_lat, prev_lon,
                       df[lat].to_numpy(), df[lon].to_numpy())
    with np.errstate(divide="ignore", invalid="ignore"):
        v = dist / dt
    # The first row of each entity has no predecessor, so `shift` already left
    # it NaN. Nothing to blank by position, which is what the previous global
    # `v[0] = nan` did and why every later boundary kept a wrong value.
    return pd.Series(v, index=df.index, name="speed_from_pos")
