"""Geodesic primitives.

Normative tier (SPEC-04 §5.3): ``haversine_m`` is what produces
``volume.distance_km`` in a SPEC-02 manifest, and what the unit plausibility
check measures a declared speed against.

It was already here in 0.9. It was nevertheless rewritten by hand in 61 files
across the projects that consume this format, 9 of which already import
Telemachus — which is a discoverability problem rather than a missing feature,
and one of the reasons the library is now split into two named tiers.
"""

from __future__ import annotations

import numpy as np

__all__ = ["haversine_m"]

#: Mean Earth radius, IUGG. The same constant every hand-written copy uses.
EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Elementwise great-circle distance in metres between two positions.

    Spherical, not ellipsoidal: at the distances between two consecutive
    telematics fixes the difference is well under the positioning error, and a
    formula that stays correct under NaN and vectorises over a whole column is
    worth more here than the last metre over a thousand kilometres.
    """
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return EARTH_RADIUS_M * c
