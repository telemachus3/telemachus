

"""
JSON Schema for Telemachus manifest (v0.1).

This schema validates the minimal YAML manifest (dataset.yaml) used by telemachus-py.
It focuses on structure and required fields; semantic checks (units consistency,
table readability, etc.) are handled in pydantic models and validate.py.

Conventions:
- All table paths are relative to the directory containing dataset.yaml.
- Tables are stored as Parquet files.
"""

MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Telemachus Manifest v0.1",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "version",
        "dataset_id",
        "created_utc",
        "frequency_hz",
        "vehicle",
        "tables"
    ],
    "properties": {
        "version": {
            "type": "string",
            "description": "Telemachus manifest version (e.g., 0.1.0)"
        },
        "dataset_id": {
            "type": "string",
            "minLength": 1,
            "description": "Stable dataset identifier"
        },
        "created_utc": {
            "type": "string",
            "minLength": 1,
            "description": "Creation timestamp (ISO-8601, UTC)"
        },
        "producer": {
            "type": "string",
            "description": "Dataset producer (e.g., RoadSimulator3)"
        },
        "frequency_hz": {
            "type": "integer",
            "minimum": 1,
            "description": "Nominal sampling frequency in Hertz"
        },
        "crs": {
            "type": "string",
            "description": "Coordinate Reference System (default EPSG:4326)"
        },
        "units": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "speed": {"type": "string"},
                "acceleration": {"type": "string"},
                "gyro": {"type": "string"}
            },
            "description": "Default physical units for speed, acceleration, and gyro"
        },
        "vehicle": {
            "type": "object",
            "additionalProperties": True,
            "required": ["id", "type"],
            "properties": {
                "id": {"type": "string", "minLength": 1},
                "type": {"type": "string", "minLength": 1}
            },
            "description": "Minimal vehicle metadata"
        },
        "source": {
            "type": "object",
            "additionalProperties": True,
            "description": "Provenance (e.g., route_engine, terrain, weather)"
        },
        "tables": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "format", "path"],
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Logical table name (trajectory, imu, events, ...)"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["parquet"],
                        "description": "Storage format (currently only parquet)"
                    },
                    "path": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Relative path to the Parquet file"
                    }
                }
            },
            "description": "List of dataset tables"
        }
    }
}