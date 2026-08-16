"""
Public API for telemachus-py v0.8.

Provides: read(), validate(), sensor introspection helpers.
Aligned with SPEC-01 (Record Format) and SPEC-02 (Manifest).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from telemachus.core.accounting import check_row_accounting
from telemachus.core.breaks import check_acquisition_breaks
from telemachus.core.carrier import CarrierProfileError, resolve_carrier_profile
from telemachus.core.corrections import check_corrections
from telemachus.core.plausibility import (
    check_heading_convention,
    check_timestamps,
    check_units,
)
from telemachus.core.privacy import check_pii
from telemachus.core.provenance import (
    check_provenance_declaration,
    resolve_column_provenance,
)
from telemachus.core.schemas import (
    ALL_KNOWN_COLUMNS,
    GYRO_COLUMN_NAMES,
    IO_COLUMN_NAMES,
    MAGNETO_COLUMN_NAMES,
    MANDATORY_BY_PROFILE,
    OBD_COLUMN_NAMES,
)

# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def read(path: str | Path) -> pd.DataFrame:
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
    with open(manifest_path, encoding="utf-8") as f:
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
    profile: str | None = None,
    acc_frame: str | None = None,
    provenance: dict[str, str] | None = None,
) -> ValidationReport:
    """Validate a DataFrame against Telemachus record format.

    Parameters
    ----------
    df : pd.DataFrame
    level : str
        "basic", "strict", "manifest", or "full".
    profile : str or None
        "core", "imu", or "full". If None, auto-detect from columns.
    acc_frame : str or None
        Declared AccPeriod frame (SPEC-02 §3.7), passed to the unit
        plausibility check so it can tell a compensated frame from a raw one
        left in g. :func:`validate_dataset` supplies it from the manifest.
    provenance : dict or None
        `column_provenance` from the manifest (SPEC-02 §3.15). It turns the
        speed cross-check from a guess into a check on the declaration: a
        column declared `measured` that tracks its own positions exactly is a
        contradiction, not a suspicion. :func:`validate_dataset` supplies it.

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

    # Rule 5: heading_deg range. "Out of range" alone sends the producer looking
    # for corrupt data, when the usual cause is a different convention for the
    # same measurement — and one of the three readings must NOT be normalised.
    if "heading_deg" in df.columns:
        finding = check_heading_convention(df["heading_deg"])
        if finding is not None:
            (errors if finding.severity == "error" else warnings).append(
                finding.message)

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

    # Rule 9 (SPEC-01 §3): every present column carries its specified type.
    # Not enforced here — `core.schemas.coerce_schema_dtypes` is what an adapter
    # uses to satisfy it, and a reader that rejected a float64 where the schema
    # says float32 would refuse most files in the wild for no benefit.

    # Rule 10: gyro all-or-nothing
    gyro_present = GYRO_COLUMN_NAMES & set(df.columns)
    if gyro_present and gyro_present != GYRO_COLUMN_NAMES:
        errors.append(f"Partial gyro columns: {sorted(gyro_present)}. Must have all or none of {sorted(GYRO_COLUMN_NAMES)}")

    # Rule 11: magneto all-or-nothing
    mag_present = MAGNETO_COLUMN_NAMES & set(df.columns)
    if mag_present and mag_present != MAGNETO_COLUMN_NAMES:
        errors.append(f"Partial magneto columns: {sorted(mag_present)}. Must have all or none of {sorted(MAGNETO_COLUMN_NAMES)}")

    # Rule 12: unit plausibility. Every rule above passes on a file whose
    # columns are correctly named, correctly typed and in the wrong unit; this
    # is the one that does not. Findings that name the wrong unit outright are
    # errors, the rest are warnings — see telemachus.core.plausibility.
    for finding in check_units(df, acc_frame=acc_frame, provenance=provenance):
        (errors if finding.severity == "error" else warnings).append(finding.message)

    # Rule 12b: the instants themselves. Every rule above accepts a row dated
    # 1970 without a word, and the descriptive layer downstream then reports a
    # three-minute drive as spanning fifty-six years.
    for finding in check_timestamps(df):
        (errors if finding.severity == "error" else warnings).append(finding.message)

    # Rule 13: personal data (SPEC-01 §2.4). Reported at every level so a
    # producer is never surprised by what is in their own file. It becomes an
    # error only in validate_dataset, where the manifest says whether the
    # dataset is going out.
    _, pii_warnings = check_pii(df)
    warnings.extend(pii_warnings)

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        profile=profile,
        level=level,
    )


def validate_manifest(path: str | Path) -> ValidationReport:
    """Validate a manifest.yaml against SPEC-02."""
    from jsonschema import ValidationError
    from jsonschema import validate as json_validate

    from telemachus.schemas.manifest_schema import MANIFEST_SCHEMA

    p = Path(path)
    errors = []

    if not p.exists():
        return ValidationReport(ok=False, errors=[f"Manifest not found: {p}"])

    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    try:
        json_validate(instance=data, schema=MANIFEST_SCHEMA)
    except ValidationError as e:
        errors.append(f"Schema error: {e.message} @ {list(e.path)}")

    warnings: list[str] = []

    # SPEC-02 §5.1: dataset_id, schema_version and source are all required.
    # The JSON Schema only enforces dataset_id, because a manifest missing the
    # other two is still readable and rejecting it there would give a message
    # about a schema rather than about what is missing.
    for field in ("schema_version", "source"):
        if not data.get(field):
            errors.append(f"Missing required field '{field}' (SPEC-02 §5.1)")

    # Check acc_periods consistency. `residual_g` is explicitly OPTIONAL in
    # SPEC-02 §5 rule 4 — an off-board descriptive hint, never a conformance
    # target — so its absence on a `partial` period is not an error.
    for i, ap in enumerate(data.get("acc_periods") or []):
        frame = ap.get("frame")
        if frame == "partial" and ap.get("residual_g") is None:
            warnings.append(
                f"acc_periods[{i}]: frame=partial without residual_g. The hint is "
                f"optional (SPEC-02 §5 rule 4) but it is the only quantitative "
                f"description of a partial frame")

    # Check burst sampling consistency
    accel = (data.get("sensors") or {}).get("accelerometer") or {}
    if accel.get("sampling_mode") == "burst":
        if not accel.get("burst_size"):
            errors.append("sensors.accelerometer: sampling_mode=burst requires burst_size")
        if not accel.get("burst_rate_hz"):
            errors.append("sensors.accelerometer: sampling_mode=burst requires burst_rate_hz")

    # SPEC-02 §3.8 carrier profile. Absent means `vehicle` with the taxonomy the
    # specification always had, so an existing manifest resolves unchanged.
    try:
        profile = resolve_carrier_profile(data)
    except CarrierProfileError as exc:
        errors.append(str(exc))
    else:
        declared_states = {e.get("carrier_state")
                           for e in (data.get("trip_carrier_states") or [])}
        declared_states |= set(data.get("carrier_state_summary") or {})
        unknown = sorted(s for s in declared_states
                         if s is not None and s not in profile.states)
        if unknown:
            errors.append(
                f"carrier_state(s) {unknown} are not states of the "
                f"{profile.name!r} carrier profile ({sorted(profile.states)}). "
                f"Either use a state of the profile, or declare a profile that "
                f"has them (SPEC-02 §3.8)")

    # SPEC-02 §3.9 acquisition breaks. Structure only here; the one claim the
    # data can contradict (`data_gap`) is cross-checked in validate_dataset,
    # which is the only entry point that has both halves in front of it.
    break_errors, break_warnings = check_acquisition_breaks(data)
    errors.extend(break_errors)
    warnings.extend(break_warnings)

    # SPEC-02 §3.5 row accounting. A validator only ever sees the output file,
    # so this block is its only evidence about what the adapter discarded on
    # the way in — and an unbalanced block is worse than none, since it reads
    # as an audit that was performed.
    metrics = (data.get("source") or {}).get("metrics")
    if metrics is not None:
        errors.extend(check_row_accounting(metrics))

    return ValidationReport(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        profile=data.get("profile", "imu"),
        level="manifest",
    )


def validate_dataset(
    path: str | Path,
    level: str = "full",
) -> ValidationReport:
    """Validate a complete dataset (manifest + parquet files)."""
    p = Path(path)
    manifest_path = p / "manifest.yaml" if p.is_dir() else p

    # Validate manifest
    manifest_report = validate_manifest(manifest_path)

    # Read manifest for profile
    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    profile = manifest.get("profile", "imu")

    # A single declared frame can be handed to the unit check; several mean the
    # file changes frame partway through and no single magnitude describes it,
    # so the check is left to say what it sees. SPEC-02 §3.7: an absent
    # `acc_periods` means one implicit `raw` period over the whole dataset.
    periods = manifest.get("acc_periods") or []
    frames = {p.get("frame") for p in periods if p.get("frame")}
    acc_frame = frames.pop() if len(frames) == 1 else ("raw" if not periods else None)

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

    provenance = resolve_column_provenance(manifest)
    data_report = validate(df, level=level, profile=profile, acc_frame=acc_frame,
                           provenance=provenance)

    # SPEC-02 §5 rule 11 — only reachable here, where manifest and data meet.
    cross_errors: list[str] = []
    cross_warnings: list[str] = []
    if level == "full":
        cross_errors, _ = check_acquisition_breaks(manifest, df)
        # SPEC-02 §5 rules 12-13 / SPEC-01 §3 rule 13: the correction
        # declaration and the columns it describes only meet here.
        correction_errors, cross_warnings = check_corrections(manifest, df)
        cross_errors += correction_errors
        # SPEC-02 §3.15: the declaration itself, before anything is inferred.
        prov_errors, prov_warnings = check_provenance_declaration(
            manifest, df, profile=profile)
        cross_errors += prov_errors
        cross_warnings += prov_warnings

    # SPEC-01 §2.4 / SPEC-04 §5.1. The manifest is where the intent to publish
    # is on record, so this is the only place the check has standing to refuse.
    # When it does refuse, drop the warning `validate()` already produced about
    # the same columns: one fact, one line.
    pii_errors, _ = check_pii(df, manifest)
    if pii_errors:
        cross_errors += pii_errors
        data_report.warnings = [w for w in data_report.warnings
                                if not w.startswith("Personal data present:")]

    return ValidationReport(
        ok=manifest_report.ok and data_report.ok and not cross_errors,
        errors=manifest_report.errors + data_report.errors + cross_errors,
        warnings=manifest_report.warnings + data_report.warnings + cross_warnings,
        profile=profile,
        level=level,
    )


class ValidationReport:
    """Result of a validation check."""

    def __init__(
        self,
        ok: bool,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
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
