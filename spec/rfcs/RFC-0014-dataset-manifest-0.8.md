---
title: "RFC-0014: Dataset Manifest — Canonical File-Level Metadata"
status: Absorbed
version: "0.8"
absorbed_into: ../SPEC-02-manifest.md
author: Sébastien Edet
created: 2026-04-15
updated: 2026-04-16
discussion: https://github.com/telemachus3/telemachus-spec/discussions
---

> **ABSORBED** — The content of this RFC forms the core of [SPEC-02: Dataset Manifest](../SPEC-02-manifest.md) (2026-04-16), extended with burst sampling in sensors block and carrier_state clarified as manifest-only. This document is kept as historical reference.

# RFC-0014: Dataset Manifest — Canonical File-Level Metadata

## 1. Motivation

RFC-0013 (Telemachus Device Format) defines several fields as **per-file** rather
than per-row: `device_id`, `trip_id` (§3.1), `acc_periods` (§3.6) and
`trip_carrier_states` (§3.7). In practice, producers (RoadSimulator3
exporter, dataset curators, MQTT ingestion bridges) have been emitting
this metadata in a sidecar `manifest.yaml` or `manifest.json` file next
to the parquet signal. No RFC formalizes that sidecar format, which
creates three problems:

- **Ambiguity** : when `device_id` is absent from the parquet columns,
  consumers don't know where to look for it (env var? config? sidecar?).
- **Fragmentation** : independent producers emit manifests with
  overlapping but slightly different schemas.
- **No validation** : consumers can't reject a malformed manifest
  because there's no canonical schema to validate against.

This RFC promotes the de-facto sidecar manifest format to a
**normative** part of the Telemachus spec. It also clarifies the
**inheritance rules** that let per-row fields be derived from
manifest-level values.

## 2. Principle

> **One manifest per Telemachus dataset.** The manifest is authoritative for
> file-level metadata. Row-level columns MAY omit any field that is
> already declared at manifest level; consumers MUST resolve by falling
> back to the manifest.

A **dataset** in this RFC's sense is a coherent collection of one or
more Telemachus parquet files sharing identical sensor configuration and (in
the common case) a single device or vehicle. The manifest lives next
to the parquet(s) under the conventional name `manifest.yaml` (YAML is
preferred; JSON with identical schema is also accepted).

## 3. Manifest Schema

### 3.1 Required fields

| Field | Type | Description |
|-------|------|-------------|
| `dataset_id` | string | Globally unique identifier (lowercase, `-` or `_` separators, no spaces). Recommended pattern: `<country>_<slug>_<year>` |
| `schema_version` | string | Telemachus spec version this manifest targets, e.g. `"telemachus-0.8"` |
| `source` | object | Provenance block (see §3.5) |

All other top-level blocks are optional but strongly recommended.

### 3.2 Identification block (recommended)

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Human-readable name |
| `slug` | string | URL-safe identifier |
| `country` | string | ISO 3166-1 alpha-2 (`AT`, `BR`, `US`, `FR`…) |
| `license` | string | SPDX identifier (`CC-BY-4.0`, `CC-BY-NC-ND-4.0`, `internal`…) |
| `license_warning` | string | Free-text caveat if license is restrictive |

### 3.3 Location & period

```yaml
location:
  city: "City_Example"
  region: "Region_Example"
  lat_center: 48.8566
  lon_center: 2.3522

period:
  start: 2025-01-01T00:00:00Z
  end: present           # or ISO-8601 date-time
  notes: "Free-text"     # optional
```

### 3.4 Hardware block

Describes the telematics device(s) that produced the data. Supports
single-device or multi-device datasets.

```yaml
hardware:
  vendor: "ExampleVendor"
  model: "example_model_1"
  class: commercial      # one of: commercial | research | consumer
  protocol: "example_protocol"   # optional
  devices:
    - name: device_1
      imei: "IMEI_EXAMPLE_1"
      fleet_id: 1001
    - name: device_2
      imei: "IMEI_EXAMPLE_2"
      fleet_id: 1002
```

**Device inheritance rule** (§4.1): if the manifest declares exactly one
device in `hardware.devices`, its `name` (or `imei`) is the canonical
`device_id` for all rows that omit it. If multiple devices are declared,
the parquet file(s) MUST declare `device_id` per-row OR per-file via
filename convention (e.g. `d0_<device_name>_*.parquet`).

### 3.5 Source (provenance) — REQUIRED

```yaml
source:
  type: open_external          # open_external | live | commercial | synthetic
  url: "https://example.org/records/xxxxxx"
  citation: "Example Dataset Citation (Zenodo or similar)"
  doi: "10.xxxx/example"       # optional
  ingestion: "MQTT bridge → DuckDB → trip processor"  # for type=live
  contact: "dataset_curator_name"    # optional
  campaign: "example commercial pilot"   # optional
  download_status: "not_downloaded"  # optional: {not_downloaded, partial, complete}
  adapter_status: "not_implemented"  # optional: {not_implemented, draft, production}
```

### 3.6 Sensors

Describes per-sensor native rates and quality. Consumers use these
to size buffers and pick interpolation strategies.

```yaml
sensors:
  gps:
    rate_hz: 1                      # effective observed rate
    rate_hz_declared: 1             # manufacturer spec (optional, if diverges)
    quality: low_cost               # low_cost | survey_grade
  accelerometer:
    rate_hz: 10
    rate_native_hz: 100             # optional, if device bursts to higher rate
    range_g: 16
    has_gyroscope: false
    unit: "m/s^2"                   # default, optional
    notes: "Bursts to native rate on event trigger"
  gyroscope:
    rate_hz: 24
    unit: "rad/s"                   # or "deg/s" if the source is in deg/s
  obd2:
    available: true
    notes: "Vehicle OBD2/CAN data included"
```

**Unit convention**: if `unit` is omitted, consumers MUST assume the
Telemachus canonical units from RFC-0013 §3 (`m/s²` for accel, `rad/s` for
gyro). If `unit` explicitly differs (e.g. PVS gyroscope in `deg/s`),
the adapter is responsible for converting at load time.

### 3.7 AccPeriods (references RFC-0013 §3.6)

Declares one or more time ranges with a coherent accelerometer frame.
The format is exactly the one in RFC-0013 §3.6, hoisted to the
manifest level:

```yaml
acc_periods:
  - start: 2025-01-01T00:00:00Z
    end:   2025-03-15T12:00:00Z
    frame: compensated
    detection_method: empirical      # device-reported | auto | user | empirical | profile_change
    residual_g: 0.0                  # optional, required if frame=partial
    notes: "Initial firmware — gravity filter ON"
  - start: 2025-03-15T12:00:01Z
    end:   present
    frame: raw
    detection_method: profile_change
    notes: "After config profile change — gravity filter OFF"
```

**Default**: if `acc_periods` is omitted, consumers MUST assume a
single implicit period `{frame: "raw"}` covering the entire dataset
(matches RFC-0013 §3.6 default).

### 3.8 CarrierStates (references RFC-0013 §3.7)

Summary count (fast overview) AND/OR per-trip declarations.

```yaml
# Aggregate count — fast sanity check
carrier_state_summary:
  mounted_driving: 23
  mounted_idle: 0
  unplugged: 0
  desk: 0
  handheld: 0
  unknown: 0

# Per-trip list — authoritative when present
# (format copied verbatim from RFC-0013 §3.7)
trip_carrier_states:
  - trip_id: "T20250401_1053_001"
    carrier_state: "handheld"
    confidence: "low"
    detection_method: "fallback"
    signals:
      speed_max_ms: 1.111
      accel_norm_std_mps2: 2.711
      position_drift_m: 19.2
```

**Default**: if neither field is present, consumers MUST assume
`carrier_state: "unknown"` globally (matches RFC-0013 §3.7 validation).

### 3.9 Volume (optional, informational)

```yaml
volume:
  n_devices: 2
  n_trips: 23
  n_messages: 1932
  total_samples: 1432
  distance_km: 61.4
  duration_hours: 1.8
```

### 3.10 Data files

Enumerates the parquet files (or external location) covered by the
manifest.

```yaml
data_files:
  - path: "d0_device_1.parquet"   # relative to manifest directory
    format: parquet
    size_mb: 31
    description: "device_1, 2025-01-01 to 2025-01-12"
  - path: "../shared/telemetry.duckdb"  # or absolute reference
    format: duckdb
    description: "Source of truth for live ingestion"
```

### 3.11 Papers using (optional, for research datasets)

```yaml
papers_using:
  - paper_id: PXXX
    role: validation                  # free-form tag
    status: planned                    # planned | in_progress | published
    accept_acc_periods:                # optional filter
      - frame: raw
```

### 3.12 Tags & config history (optional)

```yaml
tags:
  - commercial
  - teltonika
  - urban

config_history:                        # for live datasets with config changes
  - timestamp: 2025-03-15T12:00:01Z
    profile: profile_v0.1
    changes:
      accelerometer_gravity:
        gravity_filter: false
```

## 4. Inheritance rules

### 4.1 Per-row fields derivable from manifest

When the following D0 per-row columns are **absent** from a parquet
file, consumers MUST resolve them as follows:

| Column | Manifest source | Fallback |
|--------|-----------------|----------|
| `device_id` | `hardware.devices[0].name` (or `.imei`) if single device | ERROR |
| `trip_id` | Parquet filename suffix (`d0_<trip_id>.parquet`) OR `source.campaign + "_" + basename` | ERROR |
| `carrier_state` | `trip_carrier_states[].carrier_state` matched by `trip_id`, else `"unknown"` | `"unknown"` |

### 4.2 Per-file flags derivable from manifest

| Flag | Source |
|------|--------|
| Accelerometer frame for sample at `ts` | First `acc_periods` entry where `start ≤ ts ≤ end`. If none match or list absent, `"raw"` |
| `is_vehicle_data` | `carrier_state ∈ {mounted_driving, mounted_idle}` |
| Gyro unit conversion | `sensors.gyroscope.unit` — if `"deg/s"`, adapter converts to `rad/s` at load |

### 4.3 Validation precedence

When a field is declared **both** per-row and in the manifest:
1. Per-row value wins for that row.
2. Consumers MUST warn if the two disagree consistently (may indicate
   a stale manifest).
3. Validators MAY reject in strict mode.

## 5. Validation Rules

A manifest is valid if:

1. `dataset_id`, `schema_version`, `source` are present.
2. `schema_version` matches the pattern `telemachus-<semver>`.
3. If `hardware.devices` has >1 entry, the dataset MUST either declare
   `device_id` per row OR use the `d0_<device_id>_*.parquet` filename
   convention.
4. If `acc_periods` is present, each entry has `start`, `end`, `frame`
   in `{raw, compensated, partial}`. For `partial`, `residual_g` is
   required.
5. If `trip_carrier_states` is present, each entry has `trip_id`,
   `carrier_state` from RFC-0013 §3.7.
6. `sensors.*.rate_hz` values are positive numbers.

A Telemachus dataset (parquet + manifest) is valid if:

7. Its manifest is valid (§5 rules 1-6).
8. For every row without a per-row `device_id`/`trip_id`, the inheritance
   rules of §4.1 resolve to a concrete value.
9. RFC-0013 validation rules (§6) apply to the parquet, using the
   manifest-declared `acc_periods` to pick the right frame per row.

## 6. Relationship to other RFCs

| RFC | Relationship |
|-----|-------------|
| RFC-0001 (Core v0.2) | This RFC formalizes the sidecar that accompanies a core-compliant file |
| RFC-0013 (D0 device layer) | This RFC hoists `acc_periods` (§3.6) and `trip_carrier_states` (§3.7) to the manifest, and clarifies `device_id`/`trip_id` per-file source |
| RFC-0007 (Validation) | Manifest validation is added to the conformance suite |
| RFC-0011 (Versioning) | `schema_version` field enforces semver binding |

## 7. Migration

### From RFC-0013 v0.7 to v0.8 (this RFC)

- **Producers** : no breaking change. If a Telemachus parquet currently embeds
  `device_id`/`trip_id` per-row, it stays valid. Producers SHOULD add a
  `manifest.yaml` sidecar to make those fields inheritable and to
  normatively declare `acc_periods` / `trip_carrier_states`.

- **Consumers** : MUST read the manifest if present and apply §4
  inheritance. MUST NOT fail on absent manifest if per-row columns are
  complete. MAY warn on absent manifest for observability.

- **Existing sidecar manifests** : those currently using
  `schema_version: telemachus-0.7` remain valid 0.7 manifests. Bumping
  to 0.8 is optional and requires only updating `schema_version`.

- **RoadSimulator3 exporter** : current output is a subset of this
  schema. Minor fields to add for full 0.8 conformance are listed in
  the RoadSimulator3 CHANGELOG.

## 8. Reference JSON Schema

See `schemas/telemachus_manifest_v0.8.json` in this repository for the
machine-validatable JSON Schema (Draft-07) that implements the rules
above. Use with `ajv` or any Draft-07-compatible validator.

## 9. References

- RFC-0001 Telemachus Core v0.2
- RFC-0013 Telemachus Device Format (v0.7)
- JSON Schema Draft-07 — https://json-schema.org/specification-links.html#draft-7

---

End of RFC-0014.
