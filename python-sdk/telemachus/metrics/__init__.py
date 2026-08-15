"""Normative tier — measurements that fill a manifest field or serve a rule.

Every function exported here answers the scope test of SPEC-04 §5.3 with a
field or a rule, not with "none":

============================  ==============================================
Function                      What it fills or serves
============================  ==============================================
``haversine_m``               ``volume.distance_km``; the speed cross-check
``path_length_m``             ``volume.distance_km``
``gaps``, ``gap_profile``     ``sensors.*.rate_hz`` (observed effective rate)
``sampling_populations``      ``sensors.*.rate_hz``, per device
``epoch_s``                   timestamp handling under the above
============================  ==============================================

Because they are bound to the specification, they do not change quietly:
a change here is a specification change. Utilities that make a decision rather
than read a property live in :mod:`telemachus.analysis`.
"""

from .basic import haversine_m
from .sampling import (
    epoch_s,
    gap_profile,
    gaps,
    path_length_m,
    sampling_populations,
)

__all__ = [
    "haversine_m",
    "epoch_s",
    "gaps",
    "gap_profile",
    "sampling_populations",
    "path_length_m",
]


def __getattr__(name: str):
    """Point the moved names at their new home instead of failing on import.

    The 1.0 split moved trip segmentation, stop detection and the descriptive
    summary to :mod:`telemachus.analysis`. Raising a plain ``AttributeError``
    would leave a reader guessing; naming the new import is the difference
    between a two-minute fix and an afternoon.
    """
    moved = {
        "TripSegmenter": "trips", "by_gap": "trips", "by_stop": "trips",
        "segment_trips": "trips", "trip_profile": "trips",
        "decimation_loss": "sampling", "stops": "sampling",
        "session_contiguity": "sampling", "session_profile": "sampling",
        "stream_summary": "describe",
        "compute_dt": "derived", "speed_from_pos": "derived",
    }
    if name in moved:
        raise AttributeError(
            f"telemachus.metrics.{name} moved to telemachus.analysis in 1.0: it "
            f"makes a decision rather than filling a manifest field (SPEC-04 §5.3). "
            f"Import it as `from telemachus.analysis import {name}`."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
