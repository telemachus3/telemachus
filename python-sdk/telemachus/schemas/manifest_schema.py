"""
JSON Schema for the Telemachus manifest.

Aligned with SPEC-02: Dataset Manifest specification.
Validates manifest.yaml structure (profile, dataset_id, schema_version,
source, hardware, sensors, acc_periods, data_files, etc.).

Two conventions matter when reading this file, because both caused the shipped
0.9 validator to reject every dataset this project publishes:

*Timestamps are not strings.* A YAML loader turns an unquoted ISO 8601 date
into a ``datetime`` object before any schema sees it, so a manifest written the
way SPEC-02 §3.3 writes it arrives here as a Python object. ``_TIMESTAMP``
accepts both forms.

*Declared-but-empty is not absent.* A manifest that writes
``threshold_filter_mg: null`` is stating that the field does not apply, which
is more informative than omitting it. Every optional scalar is nullable for
that reason.
"""

# A date/time may reach the validator as an ISO 8601 string or, when PyYAML has
# already parsed it, as a datetime object. jsonschema has no type for the
# latter, so it is accepted as anything that is not a bare number.
_TIMESTAMP = {"not": {"type": ["number", "boolean", "array"]}}
_NUM = {"type": ["number", "null"]}
_POS_RATE = {"type": ["number", "null"], "exclusiveMinimum": 0}
_STR = {"type": ["string", "null"]}
_INT = {"type": ["integer", "null"]}
_BOOL = {"type": ["boolean", "null"]}

MANIFEST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Telemachus Manifest",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "dataset_id",
    ],
    "properties": {
        "dataset_id": {
            "type": "string",
            "minLength": 1,
            "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]*$",
            "description": (
                "Globally unique identifier. Pattern: <country>_<slug>_<year>, "
                "where <country> is the ISO 3166-1 alpha-2 code of SPEC-02 §3.2 "
                "and is therefore uppercase (AT_aegis_graz_2017)"
            ),
        },
        "schema_version": {
            "type": "string",
            "pattern": "^telemachus-",
            "description": "Telemachus spec version, e.g. telemachus-1.0",
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
                "start": _TIMESTAMP,
                "end": _TIMESTAMP,
                "notes": _STR,
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
                        "rate_hz": _POS_RATE,
                        "rate_hz_declared": _NUM,
                        "quality": _STR,
                    },
                },
                "accelerometer": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": _POS_RATE,
                        "rate_native_hz": _NUM,
                        "range_g": _NUM,
                        "has_gyroscope": _BOOL,
                        "unit": _STR,
                        "threshold_filter_mg": _NUM,
                        "sampling_mode": {
                            "type": "string",
                            "enum": ["continuous", "burst"],
                        },
                        "burst_size": _INT,
                        "burst_rate_hz": _NUM,
                        "notes": _STR,
                    },
                },
                "gyroscope": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": _POS_RATE,
                        "unit": _STR,
                    },
                },
                "magnetometer": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "rate_hz": _POS_RATE,
                        "unit": _STR,
                    },
                },
                "obd2": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "available": _BOOL,
                        "pids": {"type": ["array", "null"], "items": {"type": "string"}},
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
                    "start": _TIMESTAMP,
                    "end": _TIMESTAMP,
                    "frame": {
                        "type": "string",
                        "enum": ["raw", "compensated", "partial"],
                    },
                    "detection_method": _STR,
                    "residual_g": _NUM,
                    "calibration_state": {},
                    "notes": _STR,
                },
            },
        },
        "carrier_state_summary": {
            "type": "object",
            "additionalProperties": True,
        },
        # SPEC-02 §3.14. `produced_by` is opaque to this specification: a
        # producer may publish corrected data in an open format without
        # publishing how it corrects.
        "corrections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["column", "adjusted"],
                "properties": {
                    "column": {"type": "string", "minLength": 1},
                    "adjusted": {"type": "string", "minLength": 1},
                    "uncertainty": _STR,
                    "produced_by": _STR,
                    "notes": _STR,
                },
            },
        },
        # SPEC-02 §3.9. `kind` and `scope` carry no enum: the vocabulary is
        # open by design, and an unrecognised value is a warning from
        # `telemachus.core.breaks`, never a schema failure.
        "acquisition_breaks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["start", "end", "kind"],
                "properties": {
                    "start": _TIMESTAMP,
                    "end": _TIMESTAMP,
                    "kind": {"type": "string", "minLength": 1},
                    "scope": _STR,
                    "detection_method": _STR,
                    "notes": _STR,
                },
            },
        },
        # SPEC-02 §3.8: a registered profile name, or an inline declaration for
        # a carrier the specification does not cover. Absent means `vehicle`.
        "carrier_profile": {
            "oneOf": [
                {"type": "string", "minLength": 1},
                {
                    "type": "object",
                    "additionalProperties": True,
                    "required": ["name", "states"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "description": _STR,
                        "states": {
                            "type": "object",
                            "minProperties": 1,
                            "additionalProperties": {
                                "type": "string",
                                "enum": ["analysable", "optional", "excluded"],
                            },
                        },
                    },
                },
            ],
        },
        "trip_carrier_states": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": True,
                "required": ["trip_id", "carrier_state"],
                "properties": {
                    "trip_id": {"type": "string"},
                    # No enum here. The permitted states are those of the
                    # declared `carrier_profile` (SPEC-02 §3.8), which JSON
                    # Schema cannot resolve from a sibling key — and which
                    # `validate_manifest` checks with a message that names the
                    # profile and lists its states.
                    "carrier_state": {"type": "string", "minLength": 1},
                    "confidence": _STR,
                    "detection_method": _STR,
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
                    "format": {"type": "string",
                               "enum": ["parquet", "duckdb", "csv", "jsonl"]},
                    "size_mb": _NUM,
                    "description": _STR,
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
                "url": _STR,
                "citation": _STR,
                "doi": _STR,
                "download_status": {
                    "type": "string",
                    "enum": ["not_downloaded", "partial", "complete"],
                },
                "adapter_status": {
                    "type": "string",
                    "enum": ["not_implemented", "draft", "production"],
                },
                "ingestion": _STR,
                "contact": _STR,
                "campaign": _STR,
                # Row accounting, SPEC-02 §3.5. The arithmetic between these
                # numbers is checked in `telemachus.core.accounting`, not here:
                # JSON Schema can say the fields are integers, not that they
                # add up, and it is the adding up that carries the meaning.
                "metrics": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "raw_rows_in": {"type": "integer", "minimum": 0},
                        "rows_out": {"type": "integer", "minimum": 0},
                        "raw_rows_dropped": {"type": "integer", "minimum": 0},
                        "drop_reasons": {
                            "type": "object",
                            "additionalProperties": {"type": "integer", "minimum": 0},
                        },
                    },
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
