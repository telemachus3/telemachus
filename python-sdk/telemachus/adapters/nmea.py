"""NMEA 0183 adapter — the sentences a GNSS receiver actually emits.

An NMEA log is what comes out of a receiver before anyone has interpreted it,
which makes it the most common raw GNSS artefact and the one furthest from a
table. Three sentence types carry what Telemachus needs:

``RMC``
    The recommended minimum: date, time, position, speed over ground, course.
    It is the only one carrying a *date*, which is why it anchors the others.
``GGA``
    Fix quality, satellite count, HDOP, altitude above the geoid.
``VTG``
    Course and ground speed, more precisely than RMC on some receivers.

They arrive as separate sentences for the same instant, so they are merged on
the timestamp rather than concatenated: one row per fix epoch, carrying
whatever the receiver said about it. A file with GGA and no RMC has times of
day and no date; rather than guess a day, the adapter asks for one
(``date``) and refuses without it, because a dataset off by an arbitrary number
of days is worse than a dataset that failed to convert.

``gnss_valid`` records the RMC status field and the GGA fix quality. It is
carried, never acted upon: SPEC-01 §2.5 makes it advisory, and dropping rows on
it is refused by name in the row accounting.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..core.accounting import RowAccount, drop_duplicate_ts
from ..core.schemas import coerce_schema_dtypes

__all__ = ["load", "manifest"]

KNOTS_TO_MPS = 0.514444
KMH_TO_MPS = 1 / 3.6


def _checksum_ok(sentence: str) -> bool:
    """Verify the ``*hh`` trailer. A sentence without one is accepted."""
    if "*" not in sentence:
        return True
    body, _, given = sentence.partition("*")
    got = 0
    for ch in body.lstrip("$!"):
        got ^= ord(ch)
    try:
        return got == int(given.strip()[:2], 16)
    except ValueError:
        return False


def _dm_to_deg(value: str, hemisphere: str) -> float:
    """``DDMM.MMMM`` plus a hemisphere letter to signed decimal degrees."""
    if not value:
        return float("nan")
    try:
        v = float(value)
    except ValueError:
        return float("nan")
    degrees = int(v / 100)
    deg = degrees + (v - degrees * 100) / 60.0
    return -deg if hemisphere.upper() in ("S", "W") else deg


def _f(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def load(source_path, *, account: RowAccount | None = None,
         date: str | None = None, device_id: str = "nmea_receiver",
         trip_id: str | None = None) -> pd.DataFrame:
    """Read an NMEA 0183 log, or every ``*.nmea``/``*.log`` in a directory.

    Parameters
    ----------
    source_path : str or Path
        A log file or a directory of them.
    account : RowAccount or None
        Filled in with the SPEC-02 §3.5 accounting. Counted separately:
        sentences that are not one of the three understood types
        (``unsupported_sentence``), sentences whose checksum fails
        (``bad_checksum``), fix epochs with no usable position
        (``no_position``), and repeated timestamps (``duplicate_ts``).
    date : str or None
        ``YYYY-MM-DD`` for a log carrying GGA but no RMC. Required in that
        case: GGA has a time of day and no date, and the alternative to asking
        is inventing one.
    device_id, trip_id : str
        Values for the corresponding columns. ``trip_id`` defaults to the
        file's stem.

    Returns
    -------
    pd.DataFrame
        One row per fix epoch: ``ts``, ``lat``, ``lon``, ``speed_mps``, and
        whichever of ``heading_deg``, ``altitude_gps_m``, ``hdop``,
        ``n_satellites``, ``gnss_valid`` the log carried.
    """
    path = Path(source_path)
    if path.is_dir():
        files = sorted([p for p in path.iterdir()
                        if p.suffix.lower() in (".nmea", ".log", ".txt")])
    else:
        files = [path]
    if not files:
        raise FileNotFoundError(f"No NMEA log in {path}")

    epochs: dict[tuple[str, str], dict] = {}
    n_fix_sentences = n_bad_checksum = 0
    current_date = date

    for log in files:
        stem_trip = trip_id or log.stem
        with open(log, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line.startswith(("$", "!")):
                    continue
                fields = line.partition("*")[0].split(",")
                kind = fields[0][3:] if len(fields[0]) >= 6 else ""
                if not _checksum_ok(line):
                    # Only a corrupt position sentence is a lost row. A corrupt
                    # GSV never carried a fix, and counting it as one would
                    # inflate `raw_rows_in` with rows that never existed.
                    if kind in ("RMC", "GGA"):
                        n_bad_checksum += 1
                    continue
                if kind == "RMC":
                    n_fix_sentences += 1
                    current_date = _rmc(fields, epochs, stem_trip) or current_date
                elif kind == "GGA":
                    n_fix_sentences += 1
                    _gga(fields, epochs, stem_trip, current_date)
                elif kind == "VTG":
                    _vtg(fields, epochs)

    # The unit of accounting is the fix epoch, not the sentence: RMC, GGA and
    # VTG describe the same instant from three angles and produce one row
    # between them. A sentence whose checksum failed is an epoch that never
    # formed, so it counts as a row in and a row dropped; sentence types this
    # adapter does not read (GSV, GSA, ...) carry no fix and are not rows at all.
    if account is not None:
        account.raw_rows_in = len(epochs) + n_bad_checksum
        account.drop("bad_checksum", n_bad_checksum)

    rows = [r for r in epochs.values() if r.get("_date")]
    undated = len(epochs) - len(rows)
    if undated and date is None:
        raise ValueError(
            f"{undated} fix epoch(s) carry a time of day and no date: the log has "
            f"GGA sentences without a preceding RMC. Pass date='YYYY-MM-DD' — this "
            f"adapter will not guess one.")
    if account is not None:
        account.drop("no_date", undated)

    if not rows:
        if n_fix_sentences == 0 and n_bad_checksum == 0:
            raise ValueError(
                f"No RMC, GGA or VTG sentence in {path}. This adapter reads those "
                f"three; a log of GSV/GSA only carries no position.")
        return _empty()

    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["_date"] + " " + df["_time"], utc=True,
                              format="%Y-%m-%d %H%M%S.%f", errors="coerce")
    naive = df["ts"].isna()
    if naive.any():
        df.loc[naive, "ts"] = pd.to_datetime(
            df.loc[naive, "_date"] + " " + df.loc[naive, "_time"],
            utc=True, format="%Y-%m-%d %H%M%S", errors="coerce")
    df = df.drop(columns=[c for c in ("_date", "_time") if c in df.columns])

    before = len(df)
    df = df[df["ts"].notna() & df["lat"].notna() & df["lon"].notna()]
    if account is not None:
        account.drop("no_position", before - len(df))

    df["device_id"] = device_id
    df = df.sort_values("ts", kind="stable")
    df, account = drop_duplicate_ts(df, account)

    return coerce_schema_dtypes(df).reset_index(drop=True)


def _epoch(epochs: dict, time_str: str, trip: str) -> dict:
    return epochs.setdefault((trip, time_str),
                             {"_time": time_str, "trip_id": trip,
                              "lat": np.nan, "lon": np.nan, "speed_mps": np.nan})


def _rmc(f: list[str], epochs: dict, trip: str) -> str | None:
    """RMC: time, status, lat, N/S, lon, E/W, speed (knots), course, date."""
    if len(f) < 10 or not f[1]:
        return None
    row = _epoch(epochs, f[1], trip)
    row["gnss_valid"] = (f[2].upper() == "A")
    row["lat"] = _dm_to_deg(f[3], f[4])
    row["lon"] = _dm_to_deg(f[5], f[6])
    speed = _f(f[7])
    if np.isfinite(speed):
        row["speed_mps"] = speed * KNOTS_TO_MPS
    course = _f(f[8])
    if np.isfinite(course):
        row["heading_deg"] = course % 360.0
    ddmmyy = f[9]
    if len(ddmmyy) == 6 and ddmmyy.isdigit():
        # Two-digit years: NMEA 0183 predates the problem and never solved it.
        # The pivot below matches the one every receiver library uses.
        year = int(ddmmyy[4:6])
        iso = f"{2000 + year if year < 80 else 1900 + year:04d}-{ddmmyy[2:4]}-{ddmmyy[0:2]}"
        row["_date"] = iso
        return iso
    return None


def _gga(f: list[str], epochs: dict, trip: str, date: str | None) -> None:
    """GGA: time, lat, N/S, lon, E/W, quality, satellites, HDOP, altitude."""
    if len(f) < 10 or not f[1]:
        return
    row = _epoch(epochs, f[1], trip)
    if date and "_date" not in row:
        row["_date"] = date
    if not np.isfinite(row.get("lat", np.nan)):
        row["lat"] = _dm_to_deg(f[2], f[3])
        row["lon"] = _dm_to_deg(f[4], f[5])
    quality = _f(f[6])
    if np.isfinite(quality):
        row.setdefault("gnss_valid", quality > 0)
        row["x_nmea_fix_quality"] = int(quality)
    sats = _f(f[7])
    if np.isfinite(sats):
        row["n_satellites"] = int(sats)
    hdop = _f(f[8])
    if np.isfinite(hdop):
        row["hdop"] = hdop
    alt = _f(f[9])
    if np.isfinite(alt):
        row["altitude_gps_m"] = alt


def _vtg(f: list[str], epochs: dict) -> None:
    """VTG: course true, course magnetic, speed in knots, speed in km/h.

    VTG carries no time, so it refines the epoch currently being built. When a
    log has no RMC and no GGA before its first VTG there is nothing to attach
    it to, and it is skipped rather than opening an epoch with no position.
    """
    if not epochs or len(f) < 8:
        return
    row = next(reversed(epochs.values()))
    course = _f(f[1])
    if np.isfinite(course):
        row["heading_deg"] = course % 360.0
    kmh = _f(f[7])
    if np.isfinite(kmh):
        row["speed_mps"] = kmh * KMH_TO_MPS


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["ts", "lat", "lon", "speed_mps", "device_id",
                                 "trip_id"])


def manifest(source_path, *, account: RowAccount | None = None,
             rows_out: int | None = None) -> dict:
    """A SPEC-02 manifest for an NMEA conversion."""
    path = Path(source_path)
    out = {
        "dataset_id": "".join(c.lower() if c.isalnum() else "_"
                              for c in (path.stem if path.is_file() else path.name)
                              ).strip("_") or "nmea_dataset",
        "schema_version": "telemachus-1.0",
        "profile": "core",
        "sensors": {"gps": {"quality": "low_cost"}},
        "source": {"type": "open_external", "adapter_status": "draft",
                   "ingestion": "NMEA 0183 RMC/GGA/VTG"},
    }
    if account is not None and rows_out is not None:
        out["source"]["metrics"] = account.finish(rows_out=rows_out)
    return out
