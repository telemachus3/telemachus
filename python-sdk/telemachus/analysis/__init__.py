"""Convenience tier — analysis utilities outside the specified perimeter.

What lives here passes no field to a manifest and serves no validation rule. It
answers a question by making a *decision*: where a trip begins, what counts as a
stop, how much of a trace a given sampling step destroys. Those decisions are
defensible, useful and used — and they are not properties of the data, so
binding them to the specification version would freeze somebody's threshold
into a standard.

The split is the one written in SPEC-04 §5.3, and it is in the import path
rather than in a note because a note does not stop anyone. ``telemachus.metrics``
is normative and moves with the spec; ``telemachus.analysis`` is maintained and
moves on its own.

Everything here reads a Telemachus-conformant frame and returns a frame or a
series. Nothing here writes one.
"""

from .derived import compute_dt, speed_from_pos
from .describe import stream_summary
from .sampling import (decimation_loss, phase_profile, session_contiguity,
                       session_profile, stops)
from .trips import TripSegmenter, by_gap, by_stop, segment_trips, trip_profile

__all__ = [
    # trip reconstruction — a decision, not a property
    "TripSegmenter",
    "by_gap",
    "by_stop",
    "segment_trips",
    "trip_profile",
    # cadence analysis
    "decimation_loss",
    "phase_profile",
    "stops",
    "session_contiguity",
    "session_profile",
    # description
    "stream_summary",
    # derived quantities
    "compute_dt",
    "speed_from_pos",
]
