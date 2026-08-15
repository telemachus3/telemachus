"""Acquisition breaks — declaring that the acquisition, not the movement, stopped.

A Telemachus file with no rows between two instants is ambiguous, and the
readings are incompatible: the vehicle was parked underground, or the device
rebooted, or the network dropped and the frames arrive three days later, or the
GNSS lost fix while the IMU kept running. Nothing in the record separates them,
so every consumer guesses — which is how one file yields two trip counts and two
availability figures depending on who read it.

The worst case is not a hole at all. A sensor that freezes keeps emitting rows
that are present, well-formed, constant, and pass every rule in SPEC-01 §3.

This module reads the declaration that removes the guess (SPEC-02 §3.9). It
records *what happened to the acquisition*, never what to do about it: which
trips to discard, whether to interpolate, whether a reconstruction can be
trusted over the interval are decisions, and they belong to the consumer.

How a break was detected is likewise out of scope (SPEC-04 §5.2), exactly as it
is for the accelerometer frame of SPEC-02 §3.7: ``detection_method`` says that a
method was used and of what kind, and stops there.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

__all__ = [
    "REGISTERED_KINDS",
    "REGISTERED_SCOPES",
    "AcquisitionBreak",
    "BreakError",
    "resolve_acquisition_breaks",
]


class BreakError(ValueError):
    """An `acquisition_breaks` entry is not usable."""


#: SPEC-02 §3.9.3. Open vocabulary with a registered core: an unrecognised kind
#: is carried through and treated as `unknown`, so a consumer reading a dataset
#: produced against a later revision degrades instead of breaking.
REGISTERED_KINDS = {
    "data_gap": "No rows were produced at all",
    "gnss_outage": "The receiver had no fix; other sensors may have kept running",
    "sensor_frozen": "A sensor emitted, but its value stopped changing",
    "device_restart": "The device rebooted; counters and state may discontinue",
    "power_loss": "Supply interrupted",
    "clock_jump": "The device clock stepped; timestamps either side are not comparable",
    "late_delivery": "The data exists and reached the store after the window it covers",
    "config_change": "Acquisition configuration changed mid-collection",
    "unknown": "Something interrupted the acquisition and it is not known what",
}

REGISTERED_SCOPES = {"gnss", "accelerometer", "gyroscope", "magnetometer",
                     "power", "clock", "link", "obd", "device"}

#: `end` may say the interval is still open, the way `acc_periods` does.
_OPEN_END = {None, "present", "ongoing", "open"}


@dataclass(frozen=True)
class AcquisitionBreak:
    """One declared interval during which the acquisition was impaired."""

    start: pd.Timestamp
    end: pd.Timestamp | None          # None for an interval still open
    kind: str
    scope: str = "device"
    detection_method: str | None = None
    notes: str | None = None

    @property
    def registered(self) -> bool:
        return self.kind in REGISTERED_KINDS

    @property
    def open_ended(self) -> bool:
        return self.end is None

    def covers(self, ts) -> bool:
        """Whether an instant falls inside this break, bounds included."""
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize("UTC")
        else:
            t = t.tz_convert("UTC")
        if t < self.start:
            return False
        return self.end is None or t <= self.end

    def duration_s(self) -> float:
        """Seconds spanned, NaN while the interval is still open."""
        if self.end is None:
            return float("nan")
        return float((self.end - self.start).total_seconds())


def _as_utc(value, field: str, index: int) -> pd.Timestamp:
    try:
        ts = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise BreakError(
            f"acquisition_breaks[{index}].{field}: {value!r} is not a timestamp") from exc
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def resolve_acquisition_breaks(manifest: dict | None) -> list[AcquisitionBreak]:
    """Read and check `acquisition_breaks` from a manifest (SPEC-02 §3.9).

    Returns them sorted by start. An absent block is an empty list, which is
    the correct default and not the same statement as "the acquisition was
    intact" — a manifest that declares nothing has not been asked.

    Raises
    ------
    BreakError
        For a missing `start`, `end` or `kind`, an unparseable timestamp, or an
        interval that ends before it begins. An unregistered `kind` or `scope`
        is *not* an error: the vocabulary is open by design, and rejecting an
        unknown value would make every future revision a breaking change.
    """
    entries = (manifest or {}).get("acquisition_breaks") or []
    if not isinstance(entries, list):
        raise BreakError("acquisition_breaks must be a list of intervals")

    out: list[AcquisitionBreak] = []
    for i, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise BreakError(f"acquisition_breaks[{i}] must be a mapping")

        missing = [k for k in ("start", "end", "kind")
                   if k not in raw or (k != "end" and raw.get(k) in (None, ""))]
        if missing:
            raise BreakError(
                f"acquisition_breaks[{i}] is missing {missing}. An interval "
                f"without a start, an end and a kind declares nothing usable "
                f"(SPEC-02 §3.9.2)")

        start = _as_utc(raw["start"], "start", i)
        end_raw = raw.get("end")
        end = None if (end_raw in _OPEN_END) else _as_utc(end_raw, "end", i)

        if end is not None and end < start:
            raise BreakError(
                f"acquisition_breaks[{i}] ends before it starts ({end} < {start})")

        out.append(AcquisitionBreak(
            start=start, end=end, kind=str(raw["kind"]),
            scope=str(raw.get("scope") or "device"),
            detection_method=raw.get("detection_method"),
            notes=raw.get("notes"),
        ))

    return sorted(out, key=lambda b: b.start)


def check_acquisition_breaks(manifest: dict | None,
                             df: "pd.DataFrame | None" = None) -> tuple[list[str], list[str]]:
    """Validate the block, and cross-check it against the data when supplied.

    Returns ``(errors, warnings)``.

    The only claim a Telemachus file can contradict is ``data_gap``: it asserts
    that no rows exist over the interval, and the rows are right there to check.
    Every other kind describes something the record cannot refute — a frozen
    sensor still emits, a late delivery is about when data arrived rather than
    whether it exists — so they are taken at their word.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        breaks = resolve_acquisition_breaks(manifest)
    except BreakError as exc:
        return [str(exc)], []

    for i, b in enumerate(breaks):
        if not b.registered:
            warnings.append(
                f"acquisition_breaks[{i}]: kind {b.kind!r} is not one of "
                f"{sorted(REGISTERED_KINDS)}. Carried through as `unknown` — the "
                f"vocabulary is open (SPEC-02 §3.9.3), so this is a note, not a fault")
        if b.scope not in REGISTERED_SCOPES:
            warnings.append(
                f"acquisition_breaks[{i}]: scope {b.scope!r} is not one of "
                f"{sorted(REGISTERED_SCOPES)}")

    if df is None or "ts" not in getattr(df, "columns", ()) or not len(df):
        return errors, warnings

    ts = pd.to_datetime(df["ts"], utc=True, errors="coerce").dropna()
    for i, b in enumerate(breaks):
        if b.kind != "data_gap":
            continue
        upper = ts.max() if b.end is None else b.end
        inside = int(((ts >= b.start) & (ts <= upper)).sum())
        if inside:
            errors.append(
                f"acquisition_breaks[{i}] declares a data_gap from {b.start} to "
                f"{b.end}, but the file has {inside} row(s) in it. A manifest "
                f"asserting an absence the data disproves is worse than no manifest")

    return errors, warnings
