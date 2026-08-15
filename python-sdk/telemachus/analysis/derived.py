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
    """Delta t in seconds (NaN for the first row)."""
    ts = pd.to_datetime(ts, utc=True, errors="coerce")
    return ts.diff().dt.total_seconds()


def speed_from_pos(df: pd.DataFrame, *, ts: str = "ts", lat: str = "lat",
                   lon: str = "lon") -> pd.Series:
    """Speed in m/s estimated from timestamp and position, by backward difference.

    Returns a Series aligned on ``df.index``, first row NaN. Straight-line
    distance between consecutive fixes understates a curve, so this reads low
    on winding roads and at coarse cadences — enough to check a unit, not
    enough to replace a measurement.
    """
    dt = compute_dt(df[ts]).to_numpy()
    dist = haversine_m(
        df[lat].shift(1).to_numpy(), df[lon].shift(1).to_numpy(),
        df[lat].to_numpy(), df[lon].to_numpy(),
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        v = dist / dt
    if len(v):
        v[0] = np.nan
    return pd.Series(v, index=df.index, name="speed_from_pos")
