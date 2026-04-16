---
title: "RFC-0001: Telemachus Core v0.2 – Schema Evolution"
status: Deprecated
deprecated: 2026-04-16
superseded_by: ../SPEC-01-record-format.md
author: Sébastien Edet
created: 2025-10-10
discussion: https://github.com/telemachus3/telemachus-spec/discussions
---

> **DEPRECATED** — This RFC has been superseded by [SPEC-01: Telemachus Record Format](../SPEC-01-record-format.md) (2026-04-16). Kept for historical reference.

# RFC-0001: Telemachus Core v0.2 – Schema Evolution

## 1. Overview

**Telemachus Core v0.1-alpha** (released in September 2025) defines a unified schema for high-frequency mobility data (GNSS, IMU, CAN, events, context).  
This RFC proposes the **evolution toward version 0.2**, introducing modularity, interoperability, and analytical readiness — bridging simulated (RS3) and real-world fleet data.

The goal is to make Telemachus the **open pivot format** for mobility telemetry — interoperable, scalable, and self-descriptive.

---

## 2. Objectives

- Define modular schema components reusable across datasets.  
- Support both **real-world** and **simulated** sources transparently.  
- Add analytical structures (derived metrics, context, labels).  
- Enable validation, provenance tracking, and data confidence.  
- Maintain **full backward compatibility** with v0.1.

---

## 3. Summary of Key Axes

| # | Theme | Objective |
|---|--------|------------|
| 1 | Modularization & Profiles | Structure the schema into reusable blocks |
| 2 | Time & Frequency | Support high-frequency timestamps & synchronization |
| 3 | Vehicle & Powertrain | Extend to electric & hybrid vehicles |
| 4 | Trajectory & Geometry | Represent road curvature & segment data |
| 5 | Context Enrichment | Add detailed weather, road, and environment |
| 6 | Provenance & Confidence | Track sensor chain & data fusion |
| 7 | Derived & Labels | Add analytical & behavioral layers |
| 8 | Simulation Metadata | Support RS3 and other generators |
| 9 | Validation & Privacy | Ensure quality, licensing & GDPR compliance |
| 10 | Interoperability & Manifest | Enable mappings and dataset manifest files |

---

## 4. Detailed Axes

### 🧩 Axis 1 – Modularization & Profiles

- Introduce `$defs` for core reusable objects (`Position`, `Motion`, `IMU`, `Engine`, `Context`, `Source`).  
- Add a top-level field `profile`: `"core" | "fleet" | "simulated" | "contextual"`.  
- Add explicit schema versioning:
  ```json
  "schema_version": "0.2.0",
  "schema_ref": "https://github.com/telemachus3/telemachus-spec/schemas/telemachus-core-0.2.json"
  ```
- Goal: Allow validators to accept subsets of data depending on the profile.

### ⏱️ Axis 2 – Time & Frequency

Axis 2 focuses on precise temporal alignment and frequency support for high-rate telemetry.  
Key goals:
- Support high-frequency timestamps (sub-ms, ns precision).
- Allow flexible sampling rates (Hz, event-based, asynchronous).
- Synchronize multiple sensor streams (GNSS, IMU, CAN, etc.).

**Example:**
```json
"timestamp": "2025-10-10T14:23:01.123456Z",
"timestamp_ns": 1696947781123456789,
"sampling_rate_hz": 100,
"sync_group": "imu_gnss"
```

**Explanation:**  
This enables robust time alignment and resampling for analytics and sensor fusion.

---

### 🚗 Axis 3 – Vehicle & Powertrain

Axis 3 extends the schema to support a wide range of vehicle types, including internal combustion, electric, and hybrid powertrains.

**Example:**
```json
"powertrain": {
  "engine": {
    "rpm": 2500,
    "load_pct": 70
  },
  "ev": {
    "soc_pct": 82.5,
    "battery_temp_c": 32.1,
    "power_kw": 45.2,
    "regen_kw": -5.7
  },
  "hybrid_mode": "charge-sustain"
}
```

**Explanation:**  
This unified block supports data from ICE, EV, and hybrid vehicles under a single schema, facilitating cross-fleet analyses.

---

### 🛣️ Axis 4 – Trajectory & Geometry

- Add a new trajectory block:
```json
"trajectory": {
  "curvature_radm": "number",
  "radius_m": "number",
  "road_class": "string",
  "segment_id": "string",
  "distance_m": "number",
  "lane_count": "integer"
}
```

- Aligns with Road Genome research and curvature datasets.

---

### 🌍 Axis 5 – Context Enrichment

- Evolve context → enrichments:
```json
"enrichments": {
  "weather": { "temp_c": "number", "precip_mm": "number", "wind_speed_ms": "number", "visibility_km": "number" },
  "road": { "surface_type": "string", "friction_coeff": "number", "speed_limit_kph": "number" },
  "environment": { "altitude_source": "string", "urban_class": "string" },
  "confidence": "number"
}
```

- Adds richer environmental and operational context.

---

### 🔗 Axis 6 – Provenance & Confidence

- Rename source → provenance:
```json
"provenance": {
  "provider": "string",
  "device_id": "string",
  "firmware": "string",
  "sampling_strategy": "string",
  "confidence": "number",
  "fusion_level": "string"
}
```

- Supports multi-source fusion and transparent traceability.

---

### 🧠 Axis 7 – Derived & Labels

- Add analytical extensions:
```json
"derived": {
  "jerk_ms3": "number",
  "yaw_rate_rads": "number",
  "curvature_rate": "number"
},
"labels": {
  "road_type": "string",
  "driver_behavior": "string",
  "event_type": "string"
}
```

- Used for machine learning, segmentation, or simulation validation.

---

### 🧪 Axis 8 – Simulation Metadata

- Optional block for synthetic datasets:
```json
"simulator": {
  "name": "RS3",
  "version": "3.2",
  "seed": 1234,
  "noise_model": "gaussian",
  "generator": "core2-altitude"
}
```

- Allows transparent distinction between real and synthetic datasets.

---

### 🔒 Axis 9 – Validation & Privacy

- Add validation_flags: boolean checks (gps_fix_ok, imu_dropout, odometer_valid).
- Add privacy block for anonymization metadata (vehicle_id_hashed, geo_masked).
- Require a license field (CC-BY-4.0, ODbL, etc.) for open datasets.

---

### 🌐 Axis 10 – Interoperability & Manifest

Introduce a companion `manifest.json`:
```json
{
  "schema_version": "0.2.0",
  "profiles": ["core", "contextual"],
  "sampling_rate_hz": 10,
  "spatial_coverage": "France metropolitan",
  "temporal_coverage": "2024-01-01/2024-12-31",
  "sources": ["RS3", "Geotab"],
  "license": "CC-BY-4.0"
}
```

**Explanation:**  
Includes dataset-level metadata and prepares for interoperability with:
- OGC SensorThings API
- OpenTelemetry
- ISO 39030 Vehicle Data Standard

---

## 5. Expected Impact
- Backward compatible with v0.1
- Enables lightweight and rich profiles
- Standardizes provenance and quality reporting
- Facilitates integration between simulated and real datasets
- Paves the way for public Telemachus Datasets v2.0

---

## 6. Next Steps
1. Implement `schemas/telemachus-core-0.2-draft.json`
2. Add example datasets in `examples/core-v0.2/`
3. Open discussion under RFCs category for feedback
4. Collect feedback → refine → tag v0.2-beta
5. Update documentation and validation tools in `telemachus-py`

---

## 7. References
- Telemachus Core v0.1-alpha Schema – September 2025
- RS3 Simulator Documentation – RoadSimulator3 project
- Telemachus Datasets v1.0 – telemachus-datasets
- ISO 39030, OGC SensorThings API, OpenTelemetry Trace Model

---

End of RFC-0001