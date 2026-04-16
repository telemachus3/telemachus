"""
Public API for telemachus-py v0.8.

Provides: read(), validate(), sensor introspection helpers.
Aligned with SPEC-01 (Record Format) and SPEC-02 (Manifest).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
import pyarrow.parquet as pq
import yaml

from telemachus.core.schemas import (
    MANDATORY_BY_PROFILE,
    GYRO_COLUMN_NAMES,
    MAGNETO_COLUMN_NAMES,
    OBD_COLUMN_NAMES,
    IO_COLUMN_NAMES,
    ALL_KNOWN_COLUMNS,
)

# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def read(path: Union[str, Path]) -> pd.DataFrame:
    """Read a Telemachus dataset from a manifest or parquet file.

    Parameters
    ----------
    path : str or Path
        Path to a ``manifest.yaml`` (reads referenced parquet files) or
        directly to a ``.parquet`` file.

    Returns
    -------
    pd.DataFrame
        DataFrame with Telemachus column names and SI units.
    """
    p = Path(path)

    if p.suffix in (".yaml", ".yml"):
        return _read_from_manifest(p)
    elif p.suffix == ".parquet":
        return _read_parquet(p)
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}. Expected .yaml or .parquet")


def _read_from_manifest(manifest_path: Path) -> pd.DataFrame:
    """Read parquet files referenced in a manifest.yaml."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    root = manifest_path.parent
    dfs = []

    # v0.8 format: data_files
    data_files = manifest.get("data_files", [])
    if data_files:
        for entry in data_files:
            pq_path = root / entry["path"]
            if pq_path.exists() and entry.get("format", "parquet") == "parquet":
                dfs.append(_read_parquet(pq_path))

    # v0.1 compat: tables
    if not dfs:
        tables = manifest.get("tables", [])
        for entry in tables:
            pq_path = root / entry["path"]
            if pq_path.exists():
                dfs.append(_read_parquet(pq_path))

    # Fallback: read any parquet in the same directory
    if not dfs:
        for pq_file in sorted(root.glob("*.parquet")):
            dfs.append(_read_parquet(pq_file))

    if not dfs:
        raise FileNotFoundError(
            f"No parquet files found for manifest {manifest_path}"
        )

    return pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]


def _read_parquet(path: Path) -> pd.DataFrame:
    """Read a single parquet file, ensuring ts is UTC-aware if present."""
    df = pd.read_parquet(path)
    if "ts" in df.columns and not hasattr(df["ts"].dtype, "tz"):
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Sensor introspection (data-level)
# ---------------------------------------------------------------------------

def _has_non_nan(df: pd.DataFrame, columns: set[str]) -> bool:
    """True if ALL named columns exist in df AND at least one row has non-NaN."""
    if not columns.issubset(df.columns):
        return False
    return df[list(columns)].notna().any(axis=None)


def has_gps(df: pd.DataFrame) -> bool:
    """True if lat, lon, speed_mps have non-NaN values."""
    return _has_non_nan(df, {"lat", "lon", "speed_mps"})


def has_imu(df: pd.DataFrame) -> bool:
    """True if ax, ay, az have non-NaN values."""
    return _has_non_nan(df, {"ax_mps2", "ay_mps2", "az_mps2"})


def has_gyro(df: pd.DataFrame) -> bool:
    """True if gx, gy, gz are present and have non-NaN values."""
    return _has_non_nan(df, GYRO_COLUMN_NAMES)


def has_magneto(df: pd.DataFrame) -> bool:
    """True if mx, my, mz are present and have non-NaN values."""
    return _has_non_nan(df, MAGNETO_COLUMN_NAMES)


def has_obd(df: pd.DataFrame) -> bool:
    """True if any OBD column (speed_obd_mps, rpm, odometer_m) has non-NaN."""
    for col in OBD_COLUMN_NAMES:
        if col in df.columns and df[col].notna().any():
            return True
    return False


def has_io(df: pd.DataFrame) -> bool:
    """True if ignition or vehicle_voltage_v is present and non-NaN."""
    for col in IO_COLUMN_NAMES:
        if col in df.columns and df[col].notna().any():
            return True
    return False


def sensor_profile(df: pd.DataFrame) -> str:
    """Return a human-readable sensor profile string.

    Examples: "gps+imu+gyro+magneto+obd", "gps+imu", "gps"
    """
    parts = []
    if has_gps(df):
        parts.append("gps")
    if has_imu(df):
        parts.append("imu")
    if has_gyro(df):
        parts.append("gyro")
    if has_magneto(df):
        parts.append("magneto")
    if has_obd(df):
        parts.append("obd")
    if has_io(df):
        parts.append("io")
    return "+".join(parts) if parts else "empty"


def is_gps_only(df: pd.DataFrame) -> bool:
    """True if GPS data present but no IMU."""
    return has_gps(df) and not has_imu(df)


def is_full_imu(df: pd.DataFrame) -> bool:
    """True if accelerometer + gyroscope available."""
    return has_imu(df) and has_gyro(df)


# ---------------------------------------------------------------------------
# Validation (basic implementation — full impl in task 8)
# ---------------------------------------------------------------------------

def validate(
    df: pd.DataFrame,
    level: str = "basic",
    profile: Optional[str] = None,
) -> "ValidationReport":
    """Validate a DataFrame against Telemachus record format.

    Parameters
    ----------
    df : pd.DataFrame
    level : str
        "basic", "strict", "manifest", or "full".
    profile : str or None
        "core", "imu", or "full". If None, auto-detect from columns.

    Returns
    -------
    ValidationReport
    """
    errors = []
    warnings = []

    # Auto-detect profile if not specified
    if profile is None:
        if has_gyro(df):
            profile = "full"
        elif has_imu(df):
            profile = "imu"
        else:
            profile = "core"

    mandatory = MANDATORY_BY_PROFILE.get(profile, MANDATORY_BY_PROFILE["imu"])

    # Rule 1: mandatory columns present
    missing = mandatory - set(df.columns)
    if missing:
        errors.append(f"Missing mandatory columns for profile '{profile}': {sorted(missing)}")

    # Rule 2: ts monotonically increasing
    if "ts" in df.columns and len(df) > 1:
        ts = df["ts"]
        if ts.dtype == "object":
            ts = pd.to_datetime(ts, utc=True, errors="coerce")
        if not ts.is_monotonic_increasing:
            errors.append("ts is not monotonically increasing")

    # Rule 4: lat/lon bounds
    if "lat" in df.columns:
        lat = df["lat"].dropna()
        if len(lat) > 0 and ((lat < -90) | (lat > 90)).any():
            errors.append("lat out of range [-90, 90]")
    if "lon" in df.columns:
        lon = df["lon"].dropna()
        if len(lon) > 0 and ((lon < -180) | (lon > 180)).any():
            errors.append("lon out of range [-180, 180]")

    # Rule 5: heading_deg range
    if "heading_deg" in df.columns:
        h = df["heading_deg"].dropna()
        if len(h) > 0 and ((h < 0) | (h >= 360)).any():
            errors.append("heading_deg out of range [0, 360)")

    # Rule 6: speed >= 0
    for speed_col in ("speed_mps", "speed_obd_mps"):
        if speed_col in df.columns:
            s = df[speed_col].dropna()
            if len(s) > 0 and (s < 0).any():
                errors.append(f"{speed_col} contains negative values")

    # Rule 8: extra columns follow x_* convention
    known = set(ALL_KNOWN_COLUMNS.keys())
    for col in df.columns:
        if col not in known and not col.startswith("x_"):
            warnings.append(f"Unknown column '{col}' — should use x_<source>_<field> convention")

    # Rule 9: type checking for known columns
    for col in df.columns:
        if col in ALL_KNOWN_COLUMNS:
            expected_field = ALL_KNOWN_COLUMNS[col]
            # Basic type compatibility check (float vs int vs string vs bool)
            # Full PyArrow type checking deferred to strict level
            pass

    # Rule 10: gyro all-or-nothing
    gyro_present = GYRO_COLUMN_NAMES & set(df.columns)
    if gyro_present and gyro_present != GYRO_COLUMN_NAMES:
        errors.append(f"Partial gyro columns: {sorted(gyro_present)}. Must have all or none of {sorted(GYRO_COLUMN_NAMES)}")

    # Rule 11: magneto all-or-nothing
    mag_present = MAGNETO_COLUMN_NAMES & set(df.columns)
    if mag_present and mag_present != MAGNETO_COLUMN_NAMES:
        errors.append(f"Partial magneto columns: {sorted(mag_present)}. Must have all or none of {sorted(MAGNETO_COLUMN_NAMES)}")

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        profile=profile,
        level=level,
    )


def validate_manifest(path: Union[str, Path]) -> "ValidationReport":
    """Validate a manifest.yaml against SPEC-02."""
    from jsonschema import validate as json_validate, ValidationError
    from telemachus.schemas.manifest_schema import MANIFEST_SCHEMA

    p = Path(path)
    errors = []

    if not p.exists():
        return ValidationReport(ok=False, errors=[f"Manifest not found: {p}"])

    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    try:
        json_validate(instance=data, schema=MANIFEST_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema error: {e.message} @ {list(e.path)}")

    # Check acc_periods consistency
    for ap in data.get("acc_periods", []):
        if ap.get("frame") == "partial" and ap.get("residual_g") is None:
            errors.append("acc_periods: frame=partial requires residual_g")

    # Check burst sampling consistency
    accel = (data.get("sensors") or {}).get("accelerometer") or {}
    if accel.get("sampling_mode") == "burst":
        if not accel.get("burst_size"):
            errors.append("sensors.accelerometer: sampling_mode=burst requires burst_size")
        if not accel.get("burst_rate_hz"):
            errors.append("sensors.accelerometer: sampling_mode=burst requires burst_rate_hz")

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        warnings=[],
        profile=data.get("profile", "imu"),
        level="manifest",
    )


def validate_dataset(
    path: Union[str, Path],
    level: str = "full",
) -> "ValidationReport":
    """Validate a complete dataset (manifest + parquet files)."""
    p = Path(path)
    manifest_path = p / "manifest.yaml" if p.is_dir() else p

    # Validate manifest
    manifest_report = validate_manifest(manifest_path)

    # Read manifest for profile
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    profile = manifest.get("profile", "imu")

    # Read and validate data
    try:
        df = read(manifest_path)
    except Exception as e:
        return ValidationReport(
            ok=False,
            errors=manifest_report.errors + [f"Cannot read data: {e}"],
            warnings=manifest_report.warnings,
            profile=profile,
            level=level,
        )

    data_report = validate(df, level=level, profile=profile)

    return ValidationReport(
        ok=manifest_report.ok and data_report.ok,
        errors=manifest_report.errors + data_report.errors,
        warnings=manifest_report.warnings + data_report.warnings,
        profile=profile,
        level=level,
    )


class ValidationReport:
    """Result of a validation check."""

    def __init__(
        self,
        ok: bool,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
        profile: str = "imu",
        level: str = "basic",
    ):
        self.ok = ok
        self.errors = errors or []
        self.warnings = warnings or []
        self.profile = profile
        self.level = level

    def __repr__(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        return (
            f"ValidationReport({status}, profile={self.profile}, level={self.level}, "
            f"errors={len(self.errors)}, warnings={len(self.warnings)})"
        )

    def __str__(self) -> str:
        lines = [repr(self)]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN: {w}")
        return "\n".join(lines)
