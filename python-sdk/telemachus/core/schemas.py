

"""
PyArrow schemas for Telemachus v0.1 core tables.

These schemas define the canonical column names and types for each table.
"""

import pyarrow as pa

# Trajectory table: spatial + kinematics
TRAJECTORY_SCHEMA = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("lat", pa.float64(), nullable=False),
    pa.field("lon", pa.float64(), nullable=False),
    pa.field("alt", pa.float32(), nullable=True),
    pa.field("speed_mps", pa.float32(), nullable=False),
])

# IMU table: accelerations + gyroscopes
IMU_SCHEMA = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("acc_x", pa.float32(), nullable=False),
    pa.field("acc_y", pa.float32(), nullable=False),
    pa.field("acc_z", pa.float32(), nullable=False),
    pa.field("gyro_x", pa.float32(), nullable=False),
    pa.field("gyro_y", pa.float32(), nullable=False),
    pa.field("gyro_z", pa.float32(), nullable=False),
])

# Events table: discrete driving events
EVENTS_SCHEMA = pa.schema([
    pa.field("timestamp_ns", pa.int64(), nullable=False),
    pa.field("event_type", pa.string(), nullable=False),
    pa.field("severity", pa.int8(), nullable=True),
    pa.field("meta", pa.string(), nullable=True),  # JSON as string (extensible)
])