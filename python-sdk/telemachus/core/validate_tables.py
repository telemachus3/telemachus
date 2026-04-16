"""
Tabular checks for Telemachus v0.1 tables (pandas-based, no external deps).

This module validates DataFrames against the canonical expectations of the
Telemachus core tables (trajectory, imu, events) using:
- required columns (as per Arrow schemas)
- dtype coercion to canonical numeric types
- monotonic timestamps (`timestamp_ns:int64` strictly increasing)
- value ranges (lat/lon bounds, non-negative speed)
- basic IMU sanity (finite values; optional soft bounds with warnings)

It also exposes a convenience `validate_all_tables()` that runs unit checks,
invokes each table validator, and optionally checks trajectory↔IMU alignment.
"""
from __future__ import annotations

from typing import Dict, Iterable, Tuple, Optional
import warnings

import numpy as np
import pandas as pd
import pyarrow as pa

from .schemas import TRAJECTORY_SCHEMA, _IMU_SCHEMA_LEGACY as IMU_SCHEMA, EVENTS_SCHEMA
from .semantics import (
    assert_units,
    ensure_monotonic_increasing,
    check_alignment,
)
from .errors import SchemaError, SemanticError, AlignmentWarning

# -------------------------
# Generic helpers
# -------------------------

def _ensure_columns_present(df: pd.DataFrame, required: Iterable[str], table: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SchemaError(f"{table}: missing columns: {missing}")


def _coerce_numeric_dtypes(df: pd.DataFrame, schema: pa.Schema, table: str) -> pd.DataFrame:
    """Coerce DataFrame numeric dtypes to match a PyArrow schema best-effort.

    - int64 ← timestamp_ns
    - float64/float32 ← numeric columns
    - string/object left as-is
    Returns a NEW DataFrame (does not mutate input).
    Raises SchemaError if a non-numeric column cannot be coerced where numeric is expected.
    """
    df2 = df.copy()
    for field in schema:
        name = field.name
        if name not in df2.columns:
            continue
        t = field.type
        try:
            if pa.types.is_int64(t):
                df2[name] = pd.to_numeric(df2[name], errors="raise").astype("int64")
            elif pa.types.is_float64(t):
                df2[name] = pd.to_numeric(df2[name], errors="raise").astype("float64")
            elif pa.types.is_float32(t):
                df2[name] = pd.to_numeric(df2[name], errors="raise").astype("float32")
            elif pa.types.is_string(t):
                # allow any object-like; ensure string dtype
                df2[name] = df2[name].astype("string")
            else:
                # leave other types as-is for v0.1
                pass
        except Exception as e:
            raise SchemaError(f"{table}: cannot coerce column '{name}' to {t}: {e}")
    return df2


# -------------------------
# Table validators
# -------------------------

def validate_trajectory_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate trajectory table and return a coerced copy (raises on failure)."""
    required = [f.name for f in TRAJECTORY_SCHEMA if not f.nullable]
    _ensure_columns_present(df, required, table="trajectory")

    df2 = _coerce_numeric_dtypes(df, TRAJECTORY_SCHEMA, table="trajectory")

    # Monotonic timestamps
    ensure_monotonic_increasing(df2, "timestamp_ns")

    # Value ranges
    lat = df2["lat"].to_numpy()
    lon = df2["lon"].to_numpy()
    if not (np.isfinite(lat).all() and np.isfinite(lon).all()):
        raise SemanticError("trajectory: lat/lon contain NaN/inf values")
    if (lat < -90).any() or (lat > 90).any():
        raise SemanticError("trajectory: latitude out of bounds [-90, 90]")
    if (lon < -180).any() or (lon > 180).any():
        raise SemanticError("trajectory: longitude out of bounds [-180, 180]")

    if "speed_mps" in df2.columns:
        spd = df2["speed_mps"].to_numpy()
        if not np.isfinite(spd).all():
            raise SemanticError("trajectory: speed_mps contains NaN/inf")
        if (spd < 0).any():
            raise SemanticError("trajectory: speed_mps must be >= 0")

    # alt is optional; if present ensure finite
    if "alt" in df2.columns and not np.all(np.isfinite(df2["alt"])):
        raise SemanticError("trajectory: alt contains NaN/inf")

    return df2


def validate_imu_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate IMU table and return a coerced copy (raises on failure)."""
    required = [f.name for f in IMU_SCHEMA]
    _ensure_columns_present(df, required, table="imu")

    df2 = _coerce_numeric_dtypes(df, IMU_SCHEMA, table="imu")

    ensure_monotonic_increasing(df2, "timestamp_ns")

    # Finite check for all numeric columns
    for col in ["acc_x","acc_y","acc_z","gyro_x","gyro_y","gyro_z"]:
        arr = df2[col].to_numpy()
        if not np.isfinite(arr).all():
            raise SemanticError(f"imu: {col} contains NaN/inf")

    # Optional soft bounds (warn only): IMU magnitudes within reasonable range
    # Acceleration in m/s^2: typical driving |acc| < ~30; gyro in rad/s: < ~10
    soft_acc_bound = 50.0
    soft_gyro_bound = 20.0
    acc_exceeds = (
        (df2[["acc_x","acc_y","acc_z"]].abs() > soft_acc_bound).to_numpy().any()
    )
    gyro_exceeds = (
        (df2[["gyro_x","gyro_y","gyro_z"]].abs() > soft_gyro_bound).to_numpy().any()
    )
    if acc_exceeds:
        warnings.warn(
            f"imu: acceleration exceeds ±{soft_acc_bound} m/s^2 (soft bound)", AlignmentWarning
        )
    if gyro_exceeds:
        warnings.warn(
            f"imu: gyro exceeds ±{soft_gyro_bound} rad/s (soft bound)", AlignmentWarning
        )

    return df2


def validate_events_df(df: pd.DataFrame) -> pd.DataFrame:
    """Validate events table and return a coerced copy (raises on failure)."""
    required = [f.name for f in EVENTS_SCHEMA if not f.nullable]
    _ensure_columns_present(df, required, table="events")

    df2 = _coerce_numeric_dtypes(df, EVENTS_SCHEMA, table="events")

    ensure_monotonic_increasing(df2, "timestamp_ns")

    # event_type must be non-null strings
    if df2["event_type"].isna().any():
        raise SemanticError("events: event_type contains nulls")

    return df2


# -------------------------
# Dataset-level convenience
# -------------------------

def validate_all_tables(
    tables: Dict[str, pd.DataFrame],
    units: Optional[Dict[str, str]] = None,
    check_timing_alignment: bool = True,
    tolerance_ns: int = 5_000_000,
) -> Tuple[bool, str, Dict[str, pd.DataFrame]]:
    """Validate units, then each present table; optionally check trajectory↔IMU alignment.

    Parameters
    ----------
    tables : dict(name -> DataFrame)
        Expected keys: 'trajectory', 'imu', 'events' (events optional).
    units : dict or None
        Manifest units; if provided, checked against canonical v0.1 (raises UnitsError).
    check_timing_alignment : bool
        If True, run asof-based alignment metrics between trajectory and IMU.
    tolerance_ns : int
        Maximum allowed |Δt| in nanoseconds for alignment; above this triggers a warning
        (and does not fail unless an exception occurs elsewhere).

    Returns
    -------
    (ok, report, coerced_tables)
        ok : bool — overall success flag (no exceptions)
        report : str — human-readable summary of checks performed
        coerced_tables : dict — tables after dtype coercion
    """
    report_lines = []

    # Units check (if provided)
    if units is not None:
        assert_units(units)
        report_lines.append("Units OK (m/s, m/s^2, rad/s)")

    coerced: Dict[str, pd.DataFrame] = {}

    if "trajectory" in tables:
        coerced["trajectory"] = validate_trajectory_df(tables["trajectory"])    
        report_lines.append("trajectory: OK")
    else:
        report_lines.append("trajectory: MISSING")

    if "imu" in tables:
        coerced["imu"] = validate_imu_df(tables["imu"])  
        report_lines.append("imu: OK")
    else:
        report_lines.append("imu: MISSING")

    if "events" in tables:
        coerced["events"] = validate_events_df(tables["events"])  
        report_lines.append("events: OK")
    else:
        report_lines.append("events: MISSING (optional)")

    # Optional alignment check
    if check_timing_alignment and ("trajectory" in coerced and "imu" in coerced):
        metrics = check_alignment(coerced["trajectory"], coerced["imu"], tolerance_ns=tolerance_ns)
        report_lines.append(
            f"alignment: pairs={metrics['pairs']}, max|Δt|={metrics['max_delta_ns']} ns, "
            f"within={metrics['within_tolerance_ratio']:.3f}, exceeds={metrics['exceeds']}"
        )

    return True, "\n".join(report_lines), coerced
