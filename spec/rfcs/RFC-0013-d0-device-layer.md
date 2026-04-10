---
title: "RFC-0013: Telemachus Record Format — Telemetry Schema"
status: Draft
version: "0.7"
author: Sébastien Edet
created: 2026-03-25
updated: 2026-04-10
discussion: https://github.com/telemachus3/telemachus-spec/discussions
---

# RFC-0013: Telemachus Record Format — Telemetry Schema

## 1. Motivation

Telemachus Core v0.2 (RFC-0001) defines a unified 10 Hz schema for mobility data. In practice, the distinction between **raw device output** and **pipeline-enriched data** is not formalized. This leads to:

- RS3 exports containing `road_type`, `event`, `target_speed` — columns that a real device never sends
- Real device data (Teltonika FMC880) missing fields the schema expects (`heading`, `hdop`)
- No clear contract for what a "Telemachus file" should contain vs. what a "D1 file" adds

This RFC introduces a strict **layered data model** (D0→D2) where each layer has an explicit column contract. D3 (indicators) and D4 (fleet aggregation) are application-level concerns outside the scope of this RFC.

## 2. Principle

> **D0 = raw device output.** No enrichment, no interpretation, no external data.

A Telemachus file contains only what the telematics device physically measures and transmits. Any column derived from external sources (maps, DEM, algorithms) belongs to D1 or higher.

## 3. D0 Column Specification

### 3.1 Mandatory Fields

Every Telemachus-compliant file MUST contain these columns:

| Column | Type | Unit | Source | Frequency | Description |
|--------|------|------|--------|-----------|-------------|
| `ts` | datetime | UTC ISO 8601 | Device clock | IMU rate | Timestamp of the measurement frame |
| `lat` | float64 | degrees WGS84 | GNSS | GNSS rate | Latitude. NaN between GNSS ticks if GNSS rate < IMU rate |
| `lon` | float64 | degrees WGS84 | GNSS | GNSS rate | Longitude. NaN between GNSS ticks |
| `speed_mps` | float32 | m/s | GNSS | GNSS rate | Ground speed. NaN between GNSS ticks |
| `ax_mps2` | float32 | m/s² | IMU accel | IMU rate | Longitudinal acceleration (+ = forward) |
| `ay_mps2` | float32 | m/s² | IMU accel | IMU rate | Lateral acceleration (+ = left) |
| `az_mps2` | float32 | m/s² | IMU accel | IMU rate | Vertical acceleration (~9.81 at rest) |
| `device_id` | string | — | Config | per-file | Unique device identifier |
| `trip_id` | string | — | Config | per-file | Unique trip identifier |

### 3.2 Recommended Fields (GNSS metadata)

These fields SHOULD be present when the hardware provides them:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `heading_deg` | float32 | degrees [0, 360) | Course over ground (COG). NaN when stationary |
| `altitude_gps_m` | float32 | m | GNSS altitude (NMEA GGA). Typical accuracy: 10–30m |
| `hdop` | float32 | — | Horizontal dilution of precision. < 2.0 = good |
| `n_satellites` | int8 | — | Number of satellites used in fix. > 6 = reliable |

### 3.3 Optional Fields (extended IMU)

Present only if the device has the corresponding sensor:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `gx_rad_s` | float32 | rad/s | Gyroscope X (roll rate) |
| `gy_rad_s` | float32 | rad/s | Gyroscope Y (pitch rate) |
| `gz_rad_s` | float32 | rad/s | Gyroscope Z (yaw rate) |

If the device lacks a gyroscope (e.g., Teltonika FMC880), these columns MUST be absent or all-NaN. They MUST NOT be filled with zeros.

### 3.4 Optional Fields (vehicle I/O)

| Column | Type | Description |
|--------|------|-------------|
| `ignition` | bool | Vehicle ignition state (digital input) |
| `odometer_m` | float64 | Odometer reading (CAN/OBD, if available) |

### 3.5 Multi-Rate Convention

Telemachus files are timestamped at the **IMU rate** (typically 10 Hz). GNSS columns (`lat`, `lon`, `speed_mps`, `heading_deg`, etc.) contain NaN on rows where no GNSS fix is available. This is called "multi-rate D0."

Example at 10 Hz IMU + 1 Hz GNSS:

```
ts,                          lat,       lon,      speed_mps, ax_mps2, ay_mps2, az_mps2
2025-01-01T08:00:00.000Z,   49.3347,   1.3830,   5.2,       0.12,    0.03,    9.81
2025-01-01T08:00:00.100Z,   NaN,       NaN,      NaN,       0.15,   -0.01,    9.80
2025-01-01T08:00:00.200Z,   NaN,       NaN,      NaN,       0.11,    0.02,    9.82
...
2025-01-01T08:00:01.000Z,   49.3348,   1.3831,   5.3,       0.13,    0.01,    9.81
```

### 3.6 AccPeriod — Accelerometer Frame Reference

Some commercial telematics devices apply **firmware-side gravity compensation** after an internal auto-calibration phase. This means the same physical accelerometer can output data in **different reference frames** over time:

| Frame | At rest | Behaviour |
|-------|---------|-----------|
| `raw` | `az ≈ -9.81 m/s²` (gravity present) | Unprocessed sensor output |
| `compensated` | `az ≈ 0 m/s²` (gravity removed) | Firmware has subtracted gravity |
| `partial` | `az ≈ ε`, `0 < |ε| < g` | Imperfect compensation, residual gravity vector |

**Observed example** (Teltonika FMC880, IMEI IMEI_EXAMPLE_1):
- 2025-07-23 (`accelerometer.calibration.state = 0`): `||a||` ≈ 0.996 g → frame = `raw`
- 2025-08-15 onwards (`calibration.state = 3`): `||a||` ≈ 0.10 g → frame = `partial` (5.77° residual orientation error)

The frame **MUST** be tracked alongside the data because downstream stages (IMU calibration, event detection) need to know whether gravity is present in the signal.

D0 specifies an **AccPeriod** segment list at the file level. Each AccPeriod is a contiguous time range with a coherent accelerometer frame:

```yaml
acc_periods:
  - start: "2025-09-04T06:48:31.378Z"
    end:   "2025-09-04T12:04:27.978Z"
    frame: "partial"
    residual_g: 0.101            # |a| at rest, expected 0 (compensated) or 1 (raw)
    calibration_state: 3         # device-specific, optional
    detection_method: "telto.calibration.state"  # or "auto" / "user"
```

**Detection methods:**
1. **Device-reported** (preferred): if the hardware exposes a calibration state field (e.g. Teltonika `accelerometer.calibration.state`), the AccPeriod boundaries follow state transitions.
2. **Auto-detection** (fallback): the pipeline measures `|a|` over the first stationary segments and classifies the frame:
   - `|a| > 8 m/s²` → `raw`
   - `|a| < 2 m/s²` → `compensated`
   - otherwise → `partial`
3. **User override**: explicit declaration in the dataset metadata.

**Single-frame files** (most cases): the file has exactly one AccPeriod covering the full duration. The convention `frame: "raw"` is the default if no AccPeriod is specified.

**Multi-frame files** (e.g. a Teltonika that finishes its auto-calibration mid-recording): the Telemachus file MAY contain multiple AccPeriod segments. Downstream stages MUST switch their gravity model accordingly at each boundary.

**Validation rule update** (replaces §6 rule 3):
- For each AccPeriod with `frame: "raw"`: `|a|` mean at rest ≈ 9.81 ± 1.0 m/s²
- For each AccPeriod with `frame: "compensated"`: `|a|` mean at rest ≈ 0 ± 1.0 m/s²
- For each AccPeriod with `frame: "partial"`: residual `|a|` value MUST match the declared `residual_g` ± 0.05 g

### 3.7 CarrierState — Device Carrier Context

A telematics device records data continuously, but **not all of that data comes from a real driving context**. A device left on a workshop bench, manipulated by hand during testing, or temporarily unplugged from the vehicle wiring still emits messages — and those messages would otherwise pollute downstream analytics (event detection, scoring, calibration). This was the dominant failure mode observed during the early 2026 commercial pilot deployment campaign, where 2 out of 3 crash-trace episodes from a Teltonika FMC880 were generated by hand manipulation rather than real driving.

D0 introduces a `carrier_state` field that classifies each **trip** (not each sample) into one of six categories. The classification is computed by the trip detector at trip boundary creation and is propagated to every sample in that trip.

| State | Description | Vehicle context | Use for analytics |
|-------|-------------|-----------------|-------------------|
| `mounted_driving` | Device installed in vehicle, vehicle in motion | YES | YES |
| `mounted_idle` | Device installed in vehicle, vehicle stationary (parked, idling) | YES | YES (ZUPT segments) |
| `unplugged` | External power lost, signals ambiguous | UNKNOWN | OPTIONAL |
| `desk` | Device on a stable surface (workshop, office), no vehicle context | NO | NO |
| `handheld` | Device being moved by hand, high accelerometer variance, no consistent vehicle motion | NO | NO |
| `unknown` | Insufficient signals to decide | UNKNOWN | NO |

**Detection algorithm.** The classifier combines four signals when available:

1. **External power voltage** (`external.powersource.voltage` on Teltonika): if > 9 V, the device is wired to a 12 V or 24 V vehicle electrical system → `powered = true`
2. **GPS speed**: fraction of samples above the driving threshold (default 1.5 m/s ≈ 5 km/h) and absolute peak speed
3. **Accelerometer norm variance** (m/s²) over the trip: distinguishes manual shaking (variance > 0.5 m/s²) from a stable surface (variance < 0.5 m/s²)
4. **GPS position drift** (bounding-box diagonal in meters): a stationary device drifts < 15 m over the trip duration, even with GNSS noise

**Decision priority** (first match wins):

```
if speed_moving_frac > 5%  OR  speed_max > 4 × driving_threshold:
    → mounted_driving           (vehicle in motion, even with frequent stops)

if powered:
    → mounted_idle              (parked, ignition on or vehicle 12V always-on)

if not powered:
    if accel_norm_std > 0.5 m/s²:
        → handheld              (manual manipulation)
    elif position_drift < 15 m:
        → desk                  (stable surface, low motion)
    else:
        → unplugged             (transition state, ambiguous)

# Fallback (unknown power state)
if accel_norm_std > 0.5 m/s²:
    → handheld (low confidence)
elif position_drift < 15 m:
    → desk (low confidence)
else:
    → unknown
```

**Confidence levels:**
- `high`: based on a strong primary signal (vehicle motion above threshold, or vehicle power present)
- `medium`: based on the unpowered branch with clear motion signature
- `low`: fallback decision when external power signal is missing (typical of devices that don't expose `external.powersource.voltage`)

**Telemachus file representation:**

```yaml
trip_carrier_states:
  - trip_id: "T20250410_1053_001"
    carrier_state: "handheld"
    confidence: "low"
    detection_method: "fallback"
    signals:
      n_samples: 2000
      speed_moving_frac: 0.0
      speed_max_ms: 1.111
      accel_norm_mean_mps2: 11.059
      accel_norm_std_mps2: 2.711
      position_drift_m: 19.2

  - trip_id: "T20250410_1053_002"
    carrier_state: "desk"
    confidence: "low"
    detection_method: "fallback"
    signals:
      accel_norm_std_mps2: 0.282
      position_drift_m: 0.0
```

**Sample-level tagging.** Beyond the trip-level metadata, every sample in the Telemachus dataframe receives two columns derived from its trip:

| Column | Type | Values |
|--------|------|--------|
| `carrier_state` | string | one of the six states above |
| `is_vehicle_data` | bool | `True` if `carrier_state ∈ {mounted_driving, mounted_idle}` |

Downstream stages **MUST** filter on `is_vehicle_data == True` for any analytics that assume a vehicle context (event detection, scoring, KPI aggregation). The IMU calibration stage MAY use data from `desk` and `mounted_idle` trips for orientation estimation (gravity vector is meaningful as long as the device is stable).

**Detection methods (analogue to §3.6):**
1. **Powered + motion** (preferred): used when `external.powersource.voltage` is reported by the device
2. **Unpowered + motion** (next-best): used when voltage indicates no vehicle power
3. **Fallback**: used when voltage is unavailable, decision relies on accelerometer variance and GPS drift only — confidence is `low`
4. **User override**: explicit declaration in the dataset metadata

**Validation rule:** A Telemachus file MUST declare `carrier_state` for every trip, OR MUST set the global default `carrier_state: "unknown"` if no detection was performed.

### 3.8 What D0 MUST NOT Contain

The following columns are **explicitly excluded** from D0. They belong to higher layers:

| Column | Correct Layer | Reason |
|--------|--------------|--------|
| `road_type` | D1 (Road Context) | Requires map data |
| `speed_limit_kmh` | D1 (Road Context) | Requires map data |
| `altitude_dem_m` | D1 (DEM Enrichment) | Requires external DEM |
| `slope_pct` | D1 (DEM Enrichment) | Derived from DEM |
| `event` | D2 (Event Detection) | Algorithmic output |
| `sqs_global` | D1 (Signal Quality) | Computed metric |
| `lat_matched` | D1 (Map Matching) | Requires OSRM |
| `target_speed` | D3 (Indicators) | Model output |

## 4. Layer Model (D0→D2)

| Layer | Name | Input | Output | Description |
|-------|------|-------|--------|-------------|
| **D0** | Device | Hardware | Raw CSV/Parquet | What the device sends |
| **D1** | Cleaned & Contextualized | D0 | Enriched D0 + new columns | GPS interpolation, IMU calibration, map matching, DEM, SQS |
| **D2** | Events & Situations | D1 | D1 + event column + event table | Driving events, curve classification |
| *D3* | *Indicators* | — | — | *Out of scope (application-level)* |
| *D4* | *Fleet Aggregation* | — | — | *Out of scope (application-level)* |

### 4.1 D1 — Columns Added

| Column | Stage | Description |
|--------|-------|-------------|
| `lat` (interpolated) | GPS Upsampling | NaN gaps filled (linear or kinematic) |
| `interpolated` | GPS Upsampling | Boolean: true if this row was interpolated |
| `dist_m` | GPS Cleaning | Incremental haversine distance |
| `lat_matched`, `lon_matched` | Map Matching | OSRM-snapped position |
| `road_type` | Road Context | OSM road classification |
| `speed_limit_kmh` | Road Context | Regulatory speed limit |
| `urban` | Road Context | Urban zone (boolean) |
| `altitude_dem_m` | DEM Enrichment | SRTM/IGN altitude |
| `slope_pct` | DEM Enrichment | Grade (%) |
| `sqs_global` | Signal Quality | Score 0–1 |

### 4.2 D2 — Columns Added

| Column | Description |
|--------|-------------|
| `event` | Event type per row (empty if none) |
| `curve_radius_m` | Instantaneous curve radius |
| `curve_class` | Classification: hairpin / sharp / moderate / gentle / straight |

### 4.3 D2 — Event Types

| Code | Signal | Default Threshold | Category |
|------|--------|-------------------|----------|
| `HARSH_BRAKE` | ax | < -3.0 m/s² | Driving |
| `HARSH_ACCEL` | ax | > +2.5 m/s² | Driving |
| `SHARP_TURN` | gz or ay | > 0.3 rad/s or > 5.0 m/s² | Driving |
| `SPEED_BUMP` | az_delta | 3.0–5.0 m/s² | Infrastructure |
| `POTHOLE` | az_delta | > 5.0 m/s² | Infrastructure |
| `CURB` | ay + az | ay > 2.5 and az_delta > 3.0 | Infrastructure |
| `DOOR_OPEN` | gy | > 3.0 rad/s (stationary) | Logistics |
| `STOP` | speed | < 0.3 m/s for ≥ 5s | Kinematic |

### 4.4 D3/D4 — Out of Scope

D3 (indicators) and D4 (fleet aggregation) are **application-level concerns** outside the scope of this RFC. Telemachus standardizes the data format up to D2. What applications do with D2 data is implementation-specific.

## 5. Hardware Mapping

### 5.1 Teltonika FMC880 (Exobox DL100)

| Device field | Telemachus column | Notes |
|-------------|-----------|-------|
| Timestamp | `ts` | UTC |
| Latitude | `lat` | 1 Hz |
| Longitude | `lon` | 1 Hz |
| Speed | `speed_mps` | Convert from km/h |
| Course | `heading_deg` | COG 0–360° |
| Altitude | `altitude_gps_m` | NMEA GGA |
| HDOP | `hdop` | — |
| Satellites | `n_satellites` | — |
| Accel X/Y/Z | `ax_mps2` / `ay_mps2` / `az_mps2` | 10 Hz |
| Gyro | — | **Not available on FMC880** |
| Ignition | `ignition` | Digital input |

### 5.2 RoadSimulator3 (synthetic)

| RS3 field | Telemachus column | Notes |
|-----------|-----------|-------|
| timestamp | `ts` | 10 Hz uniform |
| lat, lon | `lat`, `lon` | NaN between ticks if multi-rate |
| speed | `speed_mps` | — |
| heading | `heading_deg` | Computed from trajectory |
| acc_x/y/z | `ax_mps2` / `ay_mps2` / `az_mps2` | Includes gravity on az |
| gyro_x/y/z | `gx_rad_s` / `gy_rad_s` / `gz_rad_s` | NaN if disabled |

> **Note:** RS3 also exports `road_type`, `event`, `target_speed` etc. These are **ground truth metadata** for validation (see P014), NOT part of D0.

## 6. Validation Rules

A Telemachus file is valid if:

1. All mandatory columns are present
2. `ts` is monotonically increasing
3. **Per AccPeriod (see §3.6)**, `|a|` mean at rest matches the declared frame:
   - `raw`: ≈ 9.81 ± 1.0 m/s²
   - `compensated`: ≈ 0 ± 1.0 m/s²
   - `partial`: ≈ `residual_g` ± 0.05 g
4. `lat` / `lon` are within [-90, 90] / [-180, 180] when not NaN
5. Every trip MUST have a declared `carrier_state` (see §3.7), or the global default `unknown` MUST be used
6. No enrichment columns are present (see §3.8)

## 7. Relationship to Other RFCs

| RFC | Relationship |
|-----|-------------|
| RFC-0001 (Core v0.2) | This RFC formalizes the D0 layer implicit in RFC-0001 |
| RFC-0003 (Events) | D2 event types and thresholds |
| RFC-0005 (Quality) | SQS dimensions feed from D0 quality fields (hdop, n_satellites) |
| RFC-0007 (Manifest) | D0 manifest should declare device_model and sensor capabilities |
| RFC-0009 (RS3 Pipeline) | RS3 produces Telemachus-compliant output + separate ground truth |

## 8. Migration

### From v0.1 to v0.6
Existing Telemachus files that mix D0 and D1 columns remain valid for processing. The pipeline SHOULD accept both formats. New exports SHOULD conform to the layered model.

### From v0.6 to v0.7 (CarrierState)
v0.7 adds the `carrier_state` field (§3.7). Existing v0.6 files remain valid; consumers MUST treat the absence of `carrier_state` as `unknown` (and therefore not filter on `is_vehicle_data`). Producers SHOULD compute `carrier_state` at trip detection time. Section §3.7 was inserted; the previous §3.7 ("What D0 MUST NOT Contain") becomes §3.8.

## 9. References

- Telemachus Core v0.2 (RFC-0001)
- [REDACTED_METHOD] — IMU Rectification Without Gyroscope (Edet, 2026)
- P014 — Ground Truth Validation (Edet, 2026)
- Teltonika FMC880 Technical Specification
- NMEA 0183 Standard (GGA, RMC sentences)

---

End of RFC-0013.
