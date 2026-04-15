

"""
Pydantic models for the Telemachus manifest (v0.1).

These models define the minimal, opinionated schema used by telemachus-py:
- Units: default units for speed, acceleration and gyroscope
- Vehicle: minimal vehicle metadata
- TableRef: reference to a dataset table (Parquet path)
- Manifest: top-level dataset manifest (YAML)

The Manifest is intentionally small to encourage adoption.
Tables (trajectory/imu/events/...) are stored as Parquet and validated separately.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, NonNegativeInt


class Units(BaseModel):
    """Default physical units used across the dataset."""
    speed: str = Field(default="m/s", description="Linear speed unit")
    acceleration: str = Field(default="m/s^2", description="Linear acceleration unit")
    gyro: str = Field(default="rad/s", description="Angular velocity unit")


class Vehicle(BaseModel):
    """Minimal vehicle descriptor."""
    id: str = Field(description="Opaque vehicle identifier within the dataset")
    type: str = Field(default="passenger_car", description="Vehicle category (e.g., passenger_car, van, truck, bus)")


class TableRef(BaseModel):
    """Reference to a dataset table stored as Parquet."""
    name: str = Field(description="Logical table name (e.g., trajectory, imu, events)")
    format: str = Field(default="parquet", description="Storage format; currently only 'parquet' is supported")
    path: str = Field(description="Relative path from the manifest directory to the Parquet file")


class Manifest(BaseModel):
    """
    Telemachus dataset manifest (YAML), minimal v0.1.

    Conventions:
    - Timestamps across tables use a common UTC nanoseconds clock: `timestamp_ns:int64`
    - CRS is EPSG:4326 (lat/lon) unless specified otherwise
    - All table paths are relative to the directory containing the manifest
    """
    version: str = Field(default="0.1.0", description="Telemachus manifest version")
    dataset_id: str = Field(description="Stable dataset identifier")
    created_utc: str = Field(description="Creation timestamp in ISO-8601 (UTC)")
    producer: str = Field(default="RoadSimulator3", description="Dataset producer")
    frequency_hz: NonNegativeInt = Field(default=10, description="Nominal sampling frequency in Hertz")
    crs: str = Field(default="EPSG:4326", description="Coordinate reference system for spatial data")
    units: Units = Field(default_factory=Units, description="Default physical units")
    vehicle: Vehicle = Field(description="Vehicle metadata")
    source: Dict[str, str] = Field(default_factory=dict, description="Free-form provenance (e.g., route_engine, terrain)")
    tables: List[TableRef] = Field(description="List of dataset tables with relative Parquet paths")