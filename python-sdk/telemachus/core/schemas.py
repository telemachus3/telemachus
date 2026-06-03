"""
PyArrow schemas for Telemachus v0.8 record format.

Aligned with SPEC-01: 7 functional groups, 3 profiles (core/imu/full).
Single flat record — no separate tables for trajectory/imu/events.

Column naming convention: SI unit suffix in name (e.g. speed_mps, ax_mps2).
"""

import pyarrow as pa

# ---------------------------------------------------------------------------
# Group 1 — Datetime (mandatory, all profiles)
# ---------------------------------------------------------------------------
DATETIME_FIELDS = [
    pa.field("ts", pa.timestamp("ns", tz="UTC"), nullable=False),
]

# ---------------------------------------------------------------------------
# Group 2 — GNSS (mandatory, all profiles)
# ---------------------------------------------------------------------------
GNSS_MANDATORY_FIELDS = [
    pa.field("lat", pa.float64(), nullable=True),       # NaN between GNSS ticks
    pa.field("lon", pa.float64(), nullable=True),       # NaN between GNSS ticks
    pa.field("speed_mps", pa.float32(), nullable=True), # NaN between GNSS ticks
]

GNSS_RECOMMENDED_FIELDS = [
    pa.field("heading_deg", pa.float32(), nullable=True),     # [0, 360)
    pa.field("altitude_gps_m", pa.float32(), nullable=True),
    pa.field("hdop", pa.float32(), nullable=True),
    pa.field("h_accuracy_m", pa.float32(), nullable=True),
    pa.field("n_satellites", pa.int8(), nullable=True),       # nullable Int8
    pa.field("pdop", pa.float32(), nullable=True),
    pa.field("gnss_valid", pa.bool_(), nullable=True),        # per-fix valid flag, advisory only
    pa.field("gnss_state", pa.int8(), nullable=True),         # receiver mode: off/no-fix/2D/3D
    pa.field("gnss_fix_status", pa.bool_(), nullable=True),   # fix acquired (distinct from gnss_valid)
]

# ---------------------------------------------------------------------------
# Group 3 — IMU: Accelerometer (mandatory for profiles imu/full)
# ---------------------------------------------------------------------------
ACCEL_FIELDS = [
    pa.field("ax_mps2", pa.float32(), nullable=False),
    pa.field("ay_mps2", pa.float32(), nullable=False),
    pa.field("az_mps2", pa.float32(), nullable=False),
]

# Group 3 — IMU: Gyroscope (mandatory for profile full, optional for imu)
GYRO_FIELDS = [
    pa.field("gx_rad_s", pa.float32(), nullable=True),
    pa.field("gy_rad_s", pa.float32(), nullable=True),
    pa.field("gz_rad_s", pa.float32(), nullable=True),
]

# Group 3 — IMU: Magnetometer (always optional)
MAGNETO_FIELDS = [
    pa.field("mx_uT", pa.float32(), nullable=True),
    pa.field("my_uT", pa.float32(), nullable=True),
    pa.field("mz_uT", pa.float32(), nullable=True),
]

# ---------------------------------------------------------------------------
# Group 4 — OBD-II (optional, all profiles)
# ---------------------------------------------------------------------------
OBD_FIELDS = [
    pa.field("speed_obd_mps", pa.float32(), nullable=True),  # PID 0x0D
    pa.field("rpm", pa.float32(), nullable=True),             # PID 0x0C
    pa.field("odometer_m", pa.float64(), nullable=True),      # PID 0xA6
]

# ---------------------------------------------------------------------------
# Group 5 — CAN (future, no formal fields yet)
# CAN signals use x_can_<signal> convention
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Group 6 — I/O: Digital & Analog Inputs (optional)
# ---------------------------------------------------------------------------
IO_FIELDS = [
    pa.field("ignition", pa.bool_(), nullable=True),
    pa.field("vehicle_voltage_v", pa.float32(), nullable=True),
    pa.field("moving", pa.bool_(), nullable=True),
    pa.field("instant_moving", pa.bool_(), nullable=True),
    pa.field("sleep_mode", pa.int8(), nullable=True),
]

# ---------------------------------------------------------------------------
# Group 8 — Device telemetry & diagnostics (optional)
# ---------------------------------------------------------------------------
TELEMETRY_FIELDS = [
    pa.field("battery_voltage_v", pa.float32(), nullable=True),
    pa.field("battery_current_a", pa.float32(), nullable=True),
    pa.field("battery_level_pct", pa.int8(), nullable=True),
    pa.field("gsm_signal_level", pa.int8(), nullable=True),
    pa.field("gsm_network_type", pa.string(), nullable=True),  # 2G/3G/4G
    pa.field("gsm_mcc", pa.int16(), nullable=True),
    pa.field("gsm_mnc", pa.int16(), nullable=True),
    pa.field("gsm_operator", pa.int32(), nullable=True),
]

# ---------------------------------------------------------------------------
# Group 9 — Events & provenance (optional context, never replaces measurements)
# ---------------------------------------------------------------------------
EVENT_FIELDS = [
    pa.field("event_id", pa.int16(), nullable=True),
    pa.field("event_priority", pa.int8(), nullable=True),
    pa.field("accel_calibration_state", pa.int8(), nullable=True),  # device frame state, cf RFC-0013 §3.6
]
PROVENANCE_FIELDS = [
    pa.field("codec_id", pa.int16(), nullable=True),
    pa.field("protocol_id", pa.int16(), nullable=True),
    pa.field("channel_id", pa.int32(), nullable=True),
    pa.field("ts_received_ms", pa.int64(), nullable=True),
    pa.field("segment_distance_m", pa.float64(), nullable=True),
]

# ---------------------------------------------------------------------------
# Group 7 — Extra: vendor-specific x_<source>_<field>
# Not schema-defined — validators ignore x_* columns
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Metadata (recommended, inheritable from manifest)
# ---------------------------------------------------------------------------
METADATA_FIELDS = [
    pa.field("device_id", pa.string(), nullable=True),
    pa.field("trip_id", pa.string(), nullable=True),
    # Sensitive (PII) — part of the format, but omitted/anonymized in PUBLISHED
    # open datasets (use opaque device_id). Cf SPEC-01 §2.4.
    pa.field("device_imei", pa.string(), nullable=True),
    pa.field("sim_iccid", pa.string(), nullable=True),
]

# ---------------------------------------------------------------------------
# Profile-based schema assembly
# ---------------------------------------------------------------------------
PROFILES = ("core", "imu", "full")


def schema_for_profile(profile: str = "imu", *, include_optional: bool = True) -> pa.Schema:
    """Build a PyArrow schema for the given Telemachus profile.

    Parameters
    ----------
    profile : str
        One of "core", "imu", "full".
    include_optional : bool
        If True, include recommended/optional fields (GNSS metadata,
        OBD, I/O, magnetometer, metadata). If False, only mandatory
        fields for the profile.

    Returns
    -------
    pa.Schema
    """
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile {profile!r}. Expected one of {PROFILES}")

    fields = list(DATETIME_FIELDS) + list(GNSS_MANDATORY_FIELDS)

    if profile in ("imu", "full"):
        fields += list(ACCEL_FIELDS)

    if profile == "full":
        fields += list(GYRO_FIELDS)

    if include_optional:
        fields += list(GNSS_RECOMMENDED_FIELDS)
        if profile in ("imu", "full"):
            if profile != "full":
                # gyro optional for imu profile
                fields += list(GYRO_FIELDS)
            fields += list(MAGNETO_FIELDS)
        fields += list(OBD_FIELDS)
        fields += list(IO_FIELDS)
        fields += list(TELEMETRY_FIELDS)
        fields += list(EVENT_FIELDS)
        fields += list(PROVENANCE_FIELDS)
        fields += list(METADATA_FIELDS)

    return pa.schema(fields)


# Pre-built schemas for convenience
CORE_SCHEMA = schema_for_profile("core", include_optional=False)
IMU_SCHEMA = schema_for_profile("imu", include_optional=False)
FULL_SCHEMA = schema_for_profile("full", include_optional=False)

# Complete schema with all optional fields (for validation: any present
# column must match these types)
COMPLETE_SCHEMA = schema_for_profile("full", include_optional=True)

# Column name sets for quick membership checks
MANDATORY_CORE = {f.name for f in DATETIME_FIELDS + GNSS_MANDATORY_FIELDS}
MANDATORY_IMU = MANDATORY_CORE | {f.name for f in ACCEL_FIELDS}
MANDATORY_FULL = MANDATORY_IMU | {f.name for f in GYRO_FIELDS}

MANDATORY_BY_PROFILE = {
    "core": MANDATORY_CORE,
    "imu": MANDATORY_IMU,
    "full": MANDATORY_FULL,
}

GYRO_COLUMN_NAMES = {f.name for f in GYRO_FIELDS}
MAGNETO_COLUMN_NAMES = {f.name for f in MAGNETO_FIELDS}
OBD_COLUMN_NAMES = {f.name for f in OBD_FIELDS}
IO_COLUMN_NAMES = {f.name for f in IO_FIELDS}

# All known column names (for type checking any present column)
ALL_KNOWN_COLUMNS = {f.name: f for f in COMPLETE_SCHEMA}


# Backward compat aliases (used by old validate_tables.py / tests)
# These use the v0.1 column names (timestamp_ns, acc_x, etc.)
TRAJECTORY_SCHEMA = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("lat", pa.float64(), nullable=False),
    pa.field("lon", pa.float64(), nullable=False),
    pa.field("alt", pa.float32(), nullable=True),
    pa.field("speed_mps", pa.float32(), nullable=False),
])

_IMU_SCHEMA_LEGACY = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("acc_x", pa.float32(), nullable=False),
    pa.field("acc_y", pa.float32(), nullable=False),
    pa.field("acc_z", pa.float32(), nullable=False),
    pa.field("gyro_x", pa.float32(), nullable=False),
    pa.field("gyro_y", pa.float32(), nullable=False),
    pa.field("gyro_z", pa.float32(), nullable=False),
])

EVENTS_SCHEMA = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("event_type", pa.string(), nullable=False),
    pa.field("severity", pa.int8(), nullable=True),
    pa.field("meta", pa.string(), nullable=True),
])
