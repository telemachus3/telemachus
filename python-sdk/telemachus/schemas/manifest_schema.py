"""
JSON Schema for Telemachus manifest v0.8.

Aligned with SPEC-02: Dataset Manifest specification.
Validates manifest.yaml structure (profile, dataset_id, schema_version,
source, hardware, sensors, acc_periods, data_files, etc.).
"""

MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Telemachus Manifest v0.8",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "dataset_id",
    ],
    "properties": {
        "dataset_id": {
            "type": "string",
            "minLength": 1,
            "pattern": "^[a-z0-9][a-z0-9_-]*$",
            "description": "Globally unique identifier. Pattern: <country>_<slug>_<year>",
        },
        "schema_version": {
            "type": "string",
            "pattern": "^telemachus-",
            "description": "Telemachus spec version, e.g. telemachus-0.8",
        },
        "profile": {
            "type": "string",
            "enum": ["core", "imu", "full"],
            "default": "imu",
            "description": "Device capability profile (SPEC-01 §2.2). Default: imu",
        },
        "title": {
            "type": "string",
            "description": "Human-readable dataset name",
        },
        "slug": {
            "type": "string",
            "description": "URL-safe identifier",
        },
        "country": {
            "type": "string",
            "minLength": 2,
            "maxLength": 2,
            "description": "ISO 3166-1 alpha-2 country code",
        },
        "license": {
            "type": "string",
            "description": "SPDX license identifier",
        },
        "license_warning": {
            "type": "string",
            "description": "Free-text caveat if license is restrictive",
        },
        "location": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "city": {"type": "string"},
                "region": {"type": "string"},
                "lat_center": {"type": "number"},
                "lon_center": {"type": "number"},
            },
        },
        "period": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "start": {"type": "string"},
                "end": {"type": "string"},
                "notes": {"type": "string"},
            },
        },
        "hardware": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "vendor": {"type": "string"},
                "model": {"type": "string"},
                "class": {
                    "type": "string",
                    "enum": ["commercial", "research", "smartphone"],
                },
                "protocol": {"type": "string"},
                "devices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "name": {"type": "string"},
                            "imei": {"type": "string"},
                        },
                    },
                },
            },
        },
        "sensors": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "gps": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": {"type": "number", "exclusiveMinimum": 0},
                        "rate_hz_declared": {"type": "number"},
                        "quality": {"type": "string"},
                    },
                },
                "accelerometer": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": {"type": "number", "exclusiveMinimum": 0},
                        "rate_native_hz": {"type": "number"},
                        "range_g": {"type": "number"},
                        "has_gyroscope": {"type": "boolean"},
                        "sampling_mode": {
                            "type": "string",
                            "enum": ["continuous", "burst"],
                        },
                        "burst_size": {"type": "integer"},
                        "burst_rate_hz": {"type": "number"},
                    },
                },
                "gyroscope": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": {"type": "number", "exclusiveMinimum": 0},
                        "unit": {"type": "string"},
                    },
                },
                "magnetometer": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": {"type": "number", "exclusiveMinimum": 0},
                        "unit": {"type": "string"},
                    },
                },
                "obd2": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "available": {"type": "boolean"},
                        "pids": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        },
        "acc_periods": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["start", "end", "frame"],
                "properties": {
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "frame": {
                        "type": "string",
                        "enum": ["raw", "compensated", "partial"],
                    },
                    "detection_method": {"type": "string"},
                    "residual_g": {"type": "number"},
                    "notes": {"type": "string"},
                },
            },
        },
        "carrier_state_summary": {
            "type": "object",
            "additionalProperties": True,
        },
        "trip_carrier_states": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["trip_id", "carrier_state"],
                "properties": {
                    "trip_id": {"type": "string"},
                    "carrier_state": {
                        "type": "string",
                        "enum": [
                            "mounted_driving",
                            "mounted_idle",
                            "unplugged",
                            "desk",
                            "handheld",
                            "unknown",
                        ],
                    },
                    "confidence": {"type": "string"},
                    "detection_method": {"type": "string"},
                },
            },
        },
        "volume": {
            "type": "object",
            "additionalProperties": True,
        },
        "data_files": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "format": {"type": "string", "enum": ["parquet", "duckdb"]},
                    "size_mb": {"type": "number"},
                    "description": {"type": "string"},
                },
            },
        },
        "source": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["open_external", "live", "commercial", "synthetic"],
                },
                "url": {"type": "string"},
                "citation": {"type": "string"},
                "doi": {"type": "string"},
                "download_status": {
                    "type": "string",
                    "enum": ["not_downloaded", "partial", "complete"],
                },
                "adapter_status": {
                    "type": "string",
                    "enum": ["not_implemented", "draft", "production"],
                },
            },
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "papers_using": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
            },
        },
        # Backward compat — v0.1 fields (accepted but not required)
        "version": {"type": "string"},
        "created_utc": {"type": "string"},
        "frequency_hz": {"type": ["integer", "number"]},
        "vehicle": {"type": "object", "additionalProperties": True},
        "tables": {"type": "array"},
    },
}
