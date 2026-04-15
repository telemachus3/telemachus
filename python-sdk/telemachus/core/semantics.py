"""
Semantics checks for Telemachus v0.1

This module provides:
- `assert_units(manifest_units)` to enforce canonical units (speed m/s, acceleration m/s^2, gyro rad/s)
- `ensure_monotonic_increasing(df, col)` to guarantee strictly increasing integer nanosecond timestamps
- `asof_alignment_metrics(left_df, right_df, on, tolerance_ns)` to compute nearest-neighbor
   alignment metrics between two time series (via pandas.merge_asof)
- `check_alignment(traj_df, imu_df, tolerance_ns, raise_on_exceed)` convenience wrapper for trajectory↔IMU

Notes
-----
- Time is expressed in UTC nanoseconds (`timestamp_ns:int64`).
- Tolerance defaults to 5 ms (5_000_000 ns) but can be tuned per dataset.
"""
from __future__ import annotations

from typing import Dict, Optional
import warnings

import numpy as np
import pandas as pd

from .errors import UnitsError, SemanticError, AlignmentWarning

# Canonical units for Telemachus v0.1
DEFAULT_UNITS: Dict[str, str] = {
    "speed": "m/s",
    "acceleration": "m/s^2",
    "gyro": "rad/s",
}


def assert_units(manifest_units: Optional[Dict[str, str]]) -> None:
    """Assert that manifest units are compatible with Telemachus v0.1.

    Raises
    ------
    UnitsError
        If units are missing or not matching v0.1 canonical units.
    """
    if not manifest_units:
        raise UnitsError("Manifest units are missing (expected speed, acceleration, gyro).")

    for key, canonical in DEFAULT_UNITS.items():
        val = manifest_units.get(key)
        if val is None:
            raise UnitsError(f"Missing unit for '{key}'. Expected '{canonical}'.")
        if str(val).strip() != canonical:
            raise UnitsError(
                f"Unit mismatch for '{key}': got '{val}', expected '{canonical}'."
            )


def ensure_monotonic_increasing(df: pd.DataFrame, col: str = "timestamp_ns") -> None:
    """Ensure that the given column is strictly increasing and non-null integer ns.

    Raises
    ------
    SemanticError
        If values are null, non-integer, or not strictly increasing.
    """
    if col not in df.columns:
        raise SemanticError(f"Column '{col}' not found for monotonicity check.")

    if df[col].isna().any():
        raise SemanticError(f"Column '{col}' contains NaN values.")

    values = df[col].to_numpy()
    if values.dtype.kind not in ("i", "u"):  # int or uint expected for ns
        raise SemanticError(f"Column '{col}' must be integer nanoseconds.")

    if values.size > 1 and not np.all(values[1:] > values[:-1]):
        raise SemanticError(f"Column '{col}' must be strictly increasing.")


def asof_alignment_metrics(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    on: str = "timestamp_ns",
    tolerance_ns: int = 5_000_000,
) -> Dict[str, float]:
    """Compute alignment metrics by nearest-neighbor join (merge_asof).

    Parameters
    ----------
    left_df, right_df : pd.DataFrame
        Two time-indexed tables containing column `on` as UTC nanoseconds.
    on : str
        Timestamp column name (default: 'timestamp_ns').
    tolerance_ns : int
        Maximum absolute delta (ns) to consider a match within tolerance.

    Returns
    -------
    dict
        {
          'pairs': int,                 # number of matched rows
          'max_delta_ns': int or np.nan,# maximum |Δt| among matched pairs
          'within_tolerance_ratio': float,  # ratio of pairs within tolerance
          'exceeds': int                # number of pairs exceeding tolerance
        }

    Notes
    -----
    - DataFrames are sorted by their timestamp column before alignment.
    - Uses `direction='nearest'` to minimize |Δt|.
    - We use `left_on`/`right_on` with distinct column names to keep both timestamps.
    """
    if on not in left_df.columns or on not in right_df.columns:
        raise SemanticError(f"Both DataFrames must contain '{on}'.")

    # Create sorted copies with distinct timestamp column names
    l = left_df[[on]].rename(columns={on: f"{on}_l"}).sort_values(f"{on}_l").reset_index(drop=True)
    r = right_df[[on]].rename(columns={on: f"{on}_r"}).sort_values(f"{on}_r").reset_index(drop=True)

    # Nearest-neighbor asof join
    merged = pd.merge_asof(
        l,
        r,
        left_on=f"{on}_l",
        right_on=f"{on}_r",
        direction="nearest",
    )

    # If right timestamp column is missing (no matches), return empty metrics
    if f"{on}_r" not in merged.columns:
        return {"pairs": 0, "max_delta_ns": np.nan, "within_tolerance_ratio": 0.0, "exceeds": 0}

    # Compute absolute deltas (ns) between matched pairs
    delta = (merged[f"{on}_r"] - merged[f"{on}_l"]).abs()
    matches = int(delta.notna().sum())

    if matches == 0:
        return {"pairs": 0, "max_delta_ns": np.nan, "within_tolerance_ratio": 0.0, "exceeds": 0}

    delta_ns = delta.dropna().astype("int64")
    max_delta = int(delta_ns.max())
    exceeds = int((delta_ns > tolerance_ns).sum())
    within_ratio = float((delta_ns <= tolerance_ns).mean())

    return {
        "pairs": matches,
        "max_delta_ns": max_delta,
        "within_tolerance_ratio": within_ratio,
        "exceeds": exceeds,
    }


def check_alignment(
    traj_df: pd.DataFrame,
    imu_df: pd.DataFrame,
    tolerance_ns: int = 5_000_000,
    raise_on_exceed: bool = False,
) -> Dict[str, float]:
    """Convenience alignment check for trajectory↔IMU.

    1) Validates monotonicity on both tables
    2) Computes nearest-neighbor alignment metrics
    3) Emits a warning (default) or raises if exceeded

    Returns the metrics dict from `asof_alignment_metrics`.
    """
    # Basic monotonicity first (clearer error messages)
    ensure_monotonic_increasing(traj_df, "timestamp_ns")
    ensure_monotonic_increasing(imu_df, "timestamp_ns")

    metrics = asof_alignment_metrics(traj_df, imu_df, on="timestamp_ns", tolerance_ns=tolerance_ns)

    if metrics["pairs"] == 0:
        raise SemanticError("No temporal overlap between trajectory and IMU.")

    if metrics["exceeds"] > 0:
        msg = (
            f"Alignment tolerance exceeded for {metrics['exceeds']} pairs; "
            f"max |Δt| = {metrics['max_delta_ns']} ns (tolerance={tolerance_ns} ns)."
        )
        if raise_on_exceed:
            raise SemanticError(msg)
        warnings.warn(msg, AlignmentWarning)

    return metrics
