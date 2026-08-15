"""GPX adapter — GPS Exchange Format 1.0 and 1.1.

GPX is what a phone, a bike computer, a handheld receiver or a survey app hands
back when asked for a track, and converting one is the shortest path from
"I have some traces" to "I have a Telemachus dataset". It is also the format
that says least: a track point carries a position, a time and an elevation, and
nothing else is guaranteed.

That silence is preserved rather than papered over. GPX has no speed field in
its base schema, so ``speed_mps`` is present — SPEC-01 §2.3 requires the column
— and NaN. Deriving it from consecutive positions would put a computed value in
a measurement column, which is the one thing SPEC-04 §5.2 rules out. A consumer
who wants that speed can compute it, and will know they did.

Track segments become trips: a GPX segment is exactly the "here the recording
broke" boundary that ``trip_id`` is for, and it is recorded by the device
rather than inferred by a threshold.

Extensions are read when they use the two schemas everyone actually emits —
Garmin's TrackPointExtension and the Cluetrust one — and their fields land as
``x_gpx_*`` per SPEC-01 §2.10 unless they map to a standard column.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

import pandas as pd

from ..core.accounting import RowAccount, drop_duplicate_ts
from ..core.schemas import coerce_schema_dtypes

__all__ = ["load", "manifest"]

# Extension fields that have a standard Telemachus column. Everything else in
# an extension keeps its own name under the x_gpx_ prefix.
_EXTENSION_COLUMNS = {
    "speed": ("speed_mps", 1.0),          # Cluetrust gpxdata:speed, in m/s
    "course": ("heading_deg", 1.0),
    "hdop": ("hdop", 1.0),
    "sat": ("n_satellites", 1),
}


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _flatten_extensions(node) -> dict:
    """Every leaf of an <extensions> subtree, keyed by its local tag name."""
    out: dict[str, str] = {}
    for child in node.iter():
        if len(child) == 0 and child.text and child.text.strip():
            out[_localname(child.tag)] = child.text.strip()
    return out


def load(source_path, *, account: RowAccount | None = None,
         device_id: str | None = None) -> pd.DataFrame:
    """Read a GPX file, or every ``*.gpx`` in a directory, as one frame.

    Parameters
    ----------
    source_path : str or Path
        A ``.gpx`` file or a directory of them.
    account : RowAccount or None
        Filled in with the SPEC-02 §3.5 row accounting. A track point with no
        ``<time>`` cannot be placed on the file's time axis and is dropped
        under ``no_timestamp``; repeated timestamps are dropped under
        ``duplicate_ts``.
    device_id : str or None
        Value for the ``device_id`` column. Defaults to the ``creator``
        attribute of the GPX root, which is what wrote the file.

    Returns
    -------
    pd.DataFrame
        ``ts``, ``lat``, ``lon``, ``speed_mps`` (NaN, see the module note),
        ``altitude_gps_m`` when elevations are present, ``device_id``,
        ``trip_id``, and any recognised extension.
    """
    path = Path(source_path)
    files = sorted(path.glob("*.gpx")) if path.is_dir() else [path]
    if not files:
        raise FileNotFoundError(f"No .gpx file in {path}")

    rows: list[dict] = []
    creators: list[str] = []
    n_points = 0

    for gpx_file in files:
        root = ElementTree.parse(gpx_file).getroot()
        creator = root.get("creator") or gpx_file.stem
        creators.append(creator)

        for trk_i, trk in enumerate(root.iter()):
            if _localname(trk.tag) != "trk":
                continue
            name = next((c.text for c in trk if _localname(c.tag) == "name" and c.text),
                        f"trk{trk_i}")
            segments = [s for s in trk if _localname(s.tag) == "trkseg"]
            for seg_i, seg in enumerate(segments):
                trip_id = f"{gpx_file.stem}/{name}/{seg_i}" if len(segments) > 1 \
                    else f"{gpx_file.stem}/{name}"
                for pt in seg:
                    if _localname(pt.tag) != "trkpt":
                        continue
                    n_points += 1
                    rows.append(_track_point(pt, trip_id, device_id or creator))

    if account is not None:
        account.raw_rows_in = n_points
    if not rows:
        return _empty()

    df = pd.DataFrame(rows)

    before = len(df)
    df = df[df["ts"].notna()]
    if account is not None:
        account.drop("no_timestamp", before - len(df))

    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    df = df.sort_values("ts", kind="stable")
    df, account = drop_duplicate_ts(df, account)

    if "speed_mps" not in df.columns:
        df["speed_mps"] = float("nan")

    return coerce_schema_dtypes(df).reset_index(drop=True)


def _track_point(pt, trip_id: str, device_id: str) -> dict:
    row: dict = {
        "ts": None,
        "lat": float(pt.get("lat")) if pt.get("lat") else None,
        "lon": float(pt.get("lon")) if pt.get("lon") else None,
        "trip_id": trip_id,
        "device_id": device_id,
    }
    for child in pt:
        tag = _localname(child.tag)
        text = (child.text or "").strip()
        if tag == "time" and text:
            row["ts"] = text
        elif tag == "ele" and text:
            row["altitude_gps_m"] = float(text)
        elif tag == "hdop" and text:
            row["hdop"] = float(text)
        elif tag == "sat" and text:
            row["n_satellites"] = int(float(text))
        elif tag == "extensions":
            for key, value in _flatten_extensions(child).items():
                target, scale = _EXTENSION_COLUMNS.get(key, (None, None))
                if target is not None:
                    try:
                        row[target] = float(value) * scale
                    except ValueError:
                        pass
                else:
                    row[f"x_gpx_{key.lower()}"] = value
    return row


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["ts", "lat", "lon", "speed_mps",
                                 "altitude_gps_m", "device_id", "trip_id"])


def manifest(source_path, *, account: RowAccount | None = None,
             rows_out: int | None = None) -> dict:
    """A SPEC-02 manifest for a GPX conversion.

    Deliberately thin: a GPX file states who wrote it and nothing about the
    receiver, the sampling rate or the collection campaign. Inventing those
    would produce a manifest that reads as authoritative and is not, so the
    blanks are left for whoever knows.
    """
    path = Path(source_path)
    out = {
        "dataset_id": _slug(path.stem if path.is_file() else path.name),
        "schema_version": "telemachus-1.0",
        "profile": "core",
        "source": {"type": "open_external", "adapter_status": "draft",
                   "ingestion": "GPX 1.1 track points"},
    }
    if account is not None and rows_out is not None:
        out["source"]["metrics"] = account.finish(rows_out=rows_out)
    return out


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in str(name)).strip("_") \
        or "gpx_dataset"
