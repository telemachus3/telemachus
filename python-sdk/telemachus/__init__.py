"""
Telemachus — Open Telematics Pivot Format.

Bridges high-frequency scientific kinematics and scalable fleet
analytics in a single, Parquet-native format.
"""

__version__ = "0.8.0"

from telemachus._api import (
    read,
    validate,
    validate_manifest,
    validate_dataset,
    has_gps,
    has_imu,
    has_gyro,
    has_magneto,
    has_obd,
    has_io,
    sensor_profile,
    is_gps_only,
    is_full_imu,
)

__all__ = [
    "__version__",
    "read",
    "validate",
    "validate_manifest",
    "validate_dataset",
    "has_gps",
    "has_imu",
    "has_gyro",
    "has_magneto",
    "has_obd",
    "has_io",
    "sensor_profile",
    "is_gps_only",
    "is_full_imu",
]
