"""
Pydantic models for the Telemachus manifest v0.8.

Aligned with SPEC-02: Dataset Manifest specification.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    """Dataset provenance (SPEC-02 §3.5)."""

    model_config = {"extra": "allow"}

    type: Optional[str] = Field(None, description="open_external | live | commercial | synthetic")
    url: Optional[str] = None
    citation: Optional[str] = None
    doi: Optional[str] = None
    download_status: Optional[str] = None
    adapter_status: Optional[str] = None
    ingestion: Optional[str] = None
    contact: Optional[str] = None
    campaign: Optional[str] = None


class Device(BaseModel):
    """Device in hardware block."""
    name: Optional[str] = None
    imei: Optional[str] = None


class Hardware(BaseModel):
    """Hardware block (SPEC-02 §3.4)."""
    vendor: Optional[str] = None
    model: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")
    protocol: Optional[str] = None
    devices: List[Device] = Field(default_factory=list)


class SensorGPS(BaseModel):
    rate_hz: Optional[float] = None
    rate_hz_declared: Optional[float] = None
    quality: Optional[str] = None


class SensorAccel(BaseModel):
    rate_hz: Optional[float] = None
    rate_native_hz: Optional[float] = None
    range_g: Optional[float] = None
    has_gyroscope: Optional[bool] = None
    sampling_mode: Optional[str] = None
    burst_size: Optional[int] = None
    burst_rate_hz: Optional[float] = None
    unit: Optional[str] = None


class SensorGyro(BaseModel):
    rate_hz: Optional[float] = None
    unit: Optional[str] = None


class SensorMagneto(BaseModel):
    rate_hz: Optional[float] = None
    unit: Optional[str] = None


class SensorOBD(BaseModel):
    available: Optional[bool] = None
    pids: Optional[List[str]] = None


class Sensors(BaseModel):
    """Sensors block (SPEC-02 §3.6)."""
    gps: Optional[SensorGPS] = None
    accelerometer: Optional[SensorAccel] = None
    gyroscope: Optional[SensorGyro] = None
    magnetometer: Optional[SensorMagneto] = None
    obd2: Optional[SensorOBD] = None


class AccPeriod(BaseModel):
    """Accelerometer frame period (SPEC-02 §3.7)."""
    start: str
    end: str
    frame: str = Field(description="raw | compensated | partial")
    detection_method: Optional[str] = None
    residual_g: Optional[float] = None
    notes: Optional[str] = None


class DataFile(BaseModel):
    """Data file reference (SPEC-02 §3.10)."""
    path: str
    format: str = "parquet"
    size_mb: Optional[float] = None
    description: Optional[str] = None


class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    lat_center: Optional[float] = None
    lon_center: Optional[float] = None


class Period(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    notes: Optional[str] = None


class Manifest(BaseModel):
    """Telemachus dataset manifest v0.8 (SPEC-02)."""

    model_config = {"extra": "allow", "populate_by_name": True}

    # Required for v0.8 (relaxed for v0.1 backward compat)
    dataset_id: str = Field(description="Globally unique dataset identifier")
    schema_version: Optional[str] = Field(None, description="e.g. telemachus-0.8")
    source: Optional[Source] = Field(None, description="Provenance block")

    # Profile
    profile: str = Field(default="imu", description="core | imu | full")

    # Identification (recommended)
    title: Optional[str] = None
    slug: Optional[str] = None
    country: Optional[str] = None
    license: Optional[str] = None
    license_warning: Optional[str] = None

    # Location & period
    location: Optional[Location] = None
    period: Optional[Period] = None

    # Hardware & sensors
    hardware: Optional[Hardware] = None
    sensors: Optional[Sensors] = None

    # AccPeriods
    acc_periods: Optional[List[AccPeriod]] = None

    # Carrier state
    carrier_state_summary: Optional[Dict[str, int]] = None
    trip_carrier_states: Optional[List[Dict]] = None

    # Volume
    volume: Optional[Dict] = None

    # Data files
    data_files: Optional[List[DataFile]] = None

    # Tags & papers
    tags: Optional[List[str]] = None
    papers_using: Optional[List[Dict]] = None

    # Backward compat v0.1 fields
    version: Optional[str] = None
    created_utc: Optional[str] = None
    frequency_hz: Optional[float] = None
    vehicle: Optional[Dict] = None
    tables: Optional[List[Dict]] = None
