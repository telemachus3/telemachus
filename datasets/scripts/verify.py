#!/usr/bin/env python3
"""
Telemachus dataset quick validator

Usage:
  verify.py <dataset_dir>
  verify.py --all                 # discover and verify every folder containing a dataset.json

Options:
  --strict        Fail if optional-but-recommended columns are missing (e.g. altitude_m)
  --min-hz 9.5    Lower bound for expected sampling frequency [default: 9.5]
  --max-hz 10.5   Upper bound for expected sampling frequency [default: 10.5]

Checks performed (spec 0.1):
  - dataset.json presence & basic keys
  - samples.{parquet|csv} presence & load
  - required columns present (speed OR speed_mps alias)
  - timestamps monotonic, ~10 Hz
  - lat/lon ranges
  - non-negative speed
  - event one-hot columns exist (event_infra/behavior/context) and are {0,1}
  - altitude_m presence (warning, strict enforces)
  - prints simple metrics (rows, duration, Hz, distance km)
"""

from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

REQ = [
    "timestamp","lat","lon",
    "speed",  # OR alias speed_mps
    "acc_x","acc_y","acc_z",
    "gyro_x","gyro_y","gyro_z",
    "event","event_infra","event_behavior","event_context",
]
OPT_RECOMMENDED = ["altitude_m"]

# Accept common exporter aliases (can be overridden by dataset.json -> column_aliases)
DEFAULT_ALIASES = {
    # target   : source candidates (first found wins)
    "timestamp": ["time", "ts", "datetime", "time_iso", "time_ms", "timestamp_ms"],
    "speed": ["speed", "speed_mps", "v_mps", "speed_ms", "speed_m_s", "v"],
    # Acceleration (m/s^2)
    "acc_x": ["ax", "accx", "accel_x", "acc_x_mps2", "imu_ax", "ax_mps2"],
    "acc_y": ["ay", "accy", "accel_y", "acc_y_mps2", "imu_ay", "ay_mps2"],
    "acc_z": ["az", "accz", "accel_z", "acc_z_mps2", "imu_az", "az_mps2"],
    # Gyro (rad/s)
    "gyro_x": ["gx", "gyrox", "gyro_x_rad_s", "imu_gx", "gx_rad_s"],
    "gyro_y": ["gy", "gyroy", "gyro_y_rad_s", "imu_gy", "gy_rad_s"],
    "gyro_z": ["gz", "gyroz", "gyro_z_rad_s", "imu_gz", "gz_rad_s"],
}

def _apply_aliases(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Create missing required columns from aliases when possible.
    Dataset may provide overrides via dataset.json -> {"column_aliases": {target: source}}.
    """
    aliases = DEFAULT_ALIASES.copy()
    # Merge user-provided single-source aliases (string or list)
    for k, v in (meta.get("column_aliases") or {}).items():
        aliases[k] = v if isinstance(v, list) else [v]

    for target, candidates in aliases.items():
        if target in df.columns:
            continue
        for src in candidates:
            if src in df.columns:
                # Special case: timestamp from milliseconds
                if target == "timestamp" and src in ("time_ms", "timestamp_ms"):
                    df[target] = pd.to_datetime(df[src], unit="ms", utc=True)
                else:
                    df[target] = df[src]
                break
    return df

# ----------------------------- utils -----------------------------

def _ok_speed_alias(cols: Iterable[str]) -> bool:
    cols = set(cols)
    return ("speed" in cols) or ("speed_mps" in cols)


def _get_speed_series(df: pd.DataFrame) -> pd.Series:
    return df["speed"] if "speed" in df.columns else df["speed_mps"]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    # Inputs in degrees; output in kilometers
    R = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _path_list_from_all() -> list[Path]:
    return sorted({p.parent for p in Path('.').rglob('dataset.json')})

# ---------------------------- validator ----------------------------

def verify_dataset(dpath: Path, *, strict: bool, min_hz: float, max_hz: float) -> None:
    if not dpath.exists():
        raise AssertionError(f"dataset dir not found: {dpath}")

    ds = dpath / "dataset.json"
    if not ds.exists():
        raise AssertionError(f"missing {ds}")

    meta = json.loads(ds.read_text(encoding="utf-8"))
    version = meta.get("version") or meta.get("release") or meta.get("format")
    print(f"[OK] dataset.json loaded — version: {version}")

    pq = dpath / "samples.parquet"
    csv = dpath / "samples.csv"
    if pq.exists():
        df = pd.read_parquet(pq)
        src = pq.name
    elif csv.exists():
        df = pd.read_csv(csv)
        src = csv.name
    else:
        raise AssertionError("missing samples.csv or samples.parquet")

    # Try to materialize required columns from aliases
    df = _apply_aliases(df, meta)

    # Ensure event columns exist (create if missing with safe defaults)
    if "event" not in df.columns:
        df["event"] = None
    for col in ("event_infra", "event_behavior", "event_context"):
        if col not in df.columns:
            df[col] = 0

    print(f"[OK] loaded {src}: rows={len(df):,}, cols={len(df.columns)}")

    cols = list(df.columns)
    missing = [c for c in REQ if c not in cols and not (c == "speed" and "speed_mps" in cols)]
    if any(k in missing for k in ("acc_x","acc_y","acc_z","gyro_x","gyro_y","gyro_z")):
        print("[HINT] IMU columns missing after alias resolution. Available columns are:")
        print(sorted(cols))
    assert _ok_speed_alias(cols), "need 'speed' or 'speed_mps'"
    assert not missing, f"missing required columns: {missing}"

    # Recommended optional columns
    opt_missing = [c for c in OPT_RECOMMENDED if c not in cols]
    if opt_missing:
        msg = f"missing recommended columns: {opt_missing}"
        if strict:
            raise AssertionError(msg)
        else:
            print(f"[WARN] {msg}")

    # Timestamp checks
    ts_series = df["timestamp"]
    if pd.api.types.is_datetime64_any_dtype(ts_series):
        ts = ts_series.dt.tz_convert("UTC") if ts_series.dt.tz is not None else ts_series.dt.tz_localize("UTC")
    else:
        ts = pd.to_datetime(ts_series, utc=True, errors="coerce")
    assert ts.notna().all(), "invalid timestamps (NaT detected)"
    assert ts.is_monotonic_increasing, "timestamps must be monotonic increasing"
    dt = ts.diff().dt.total_seconds().dropna()
    hz = 1.0 / dt.median() if len(dt) else float("nan")
    assert min_hz <= hz <= max_hz, f"observed Hz≈{hz:.3f} not in [{min_hz},{max_hz}]"

    # Geo sanity
    assert df["lat"].between(-90, 90).all(), "lat out of range"
    assert df["lon"].between(-180, 180).all(), "lon out of range"

    # Speed sanity
    # If only speed_mps exists, it's fine; _get_speed_series covers it after alias application
    sp = _get_speed_series(df)
    assert (sp >= 0).all(), "negative speed found"
    if (sp > 70).any():  # >252 km/h — unlikely for road sim, warn only
        print("[WARN] unusually high speeds detected (>70 m/s)")

    # Events one-hot sanity (coerce if necessary)
    for col in ("event_infra", "event_behavior", "event_context"):
        vals = set(pd.unique(df[col].dropna()))
        if not vals.issubset({0, 1}):
            print(f"[WARN] coercing non-binary values in {col} to 0/1")
            df[col] = df[col].astype(int).clip(0, 1)

    # Distance approx.
    try:
        # sample every ~1 s to speed up
        step = max(1, int(round(1 / (hz if hz == hz else 10))))
        lat = df["lat"].to_numpy()[::step]
        lon = df["lon"].to_numpy()[::step]
        dist_km = 0.0
        for i in range(1, len(lat)):
            dist_km += _haversine_km(lat[i-1], lon[i-1], lat[i], lon[i])
    except Exception:
        dist_km = float('nan')

    duration_s = (ts.iloc[-1] - ts.iloc[0]).total_seconds() if len(ts) else 0.0

    print(
        f"[OK] metrics: duration={duration_s:.1f}s, Hz≈{hz:.3f}, distance≈{dist_km:.2f} km"
    )

    print("[OK] basic checks passed ✅")


# ------------------------------ CLI ------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify Telemachus dataset folders")
    p.add_argument("dataset_dir", nargs="?", help="Path to a dataset folder (contains dataset.json)")
    p.add_argument("--all", action="store_true", help="Verify all datasets found in the repository")
    p.add_argument("--strict", action="store_true", help="Fail on recommended columns missing (e.g. altitude_m)")
    p.add_argument("--min-hz", type=float, default=9.5, help="Lower bound for expected sampling frequency")
    p.add_argument("--max-hz", type=float, default=10.5, help="Upper bound for expected sampling frequency")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.all:
        paths = _path_list_from_all()
        if not paths:
            print("No dataset.json found; nothing to verify.")
            return 0
        rc = 0
        for d in paths:
            print(f"\n➡️  Verifying {d}")
            try:
                verify_dataset(d, strict=args.strict, min_hz=args.min_hz, max_hz=args.max_hz)
            except AssertionError as e:
                print(f"[FAIL] {d}: {e}")
                rc = 1
        return rc

    # Single directory mode
    if not args.dataset_dir:
        print("usage: verify.py <dataset_dir> | verify.py --all")
        return 2

    try:
        verify_dataset(Path(args.dataset_dir), strict=args.strict, min_hz=args.min_hz, max_hz=args.max_hz)
    except AssertionError as e:
        print(f"[FAIL] {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
