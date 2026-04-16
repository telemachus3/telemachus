---
title: "SPEC-01: Telemachus Record Format — Telemetry Format"
status: Draft
version: "0.8"
author: Sébastien Edet
created: 2026-04-16
supersedes: RFC-0001, RFC-0004, RFC-0013
---

# SPEC-01: Telemachus Record Format — Telemetry Format

## 1. Introduction

Telemachus defines a **layered data model** for mobility telemetry. Each
layer has an explicit column contract separating raw device output from
pipeline-enriched data.

This specification consolidates and supersedes RFC-0001 (Core v0.2),
RFC-0004 (Extended FieldGroups), and RFC-0013 (Telemachus Device Format v0.7).

### 1.1 Design Principles

- **D0 = raw device output.** No enrichment, no interpretation, no external data.
- **Columns are flat.** No nested JSON objects — every field is a top-level column.
- **Units are SI.** m/s, m/s², rad/s, degrees WGS84, UTC nanoseconds.
- **Multi-rate is native.** GNSS and IMU may sample at different frequencies.
- **Vendor extensions welcome.** Extra columns use `x_<source>_<field>` convention.

### 1.2 Layer Overview

```mermaid
graph TD
    subgraph D0["D0 — Device (Raw)"]
        GPS[GNSS: lat, lon, speed, heading]
        IMU[IMU: accel, gyro, magneto]
        VIO[Vehicle I/O: ignition, OBD, voltage]
        EXTRA[Vendor-specific: x_source_field]
    end

    subgraph D1["D1 — Cleaned & Contextualized"]
        INTERP[GPS interpolation & map matching]
        CAL[IMU calibration & gravity alignment]
        DEM[DEM altitude & slope]
        SQS[Signal Quality Score]
    end

    subgraph D2["D2 — Events & Situations"]
        EVT[Driving events: brake, accel, turn]
        CURVE[Curve classification]
        INFRA[Infrastructure: bumps, potholes]
    end

    D0 --> D1 --> D2

    style D0 fill:#e8f5e9,stroke:#2e7d32
    style D1 fill:#e3f2fd,stroke:#1565c0
    style D2 fill:#fff3e0,stroke:#e65100
```

---

## 2. D0 — Device Layer

### 2.1 Functional Groups

Telemachus columns are organized into **five functional groups**. All columns are
flat (no nesting). The grouping is conceptual, for documentation only.

```mermaid
graph LR
    subgraph DT["Datetime"]
        ts["ts (UTC)"]
    end

    subgraph GNSS["GNSS"]
        lat & lon
        speed_mps
        heading_deg
        altitude_gps_m
        hdop & h_accuracy_m
        n_satellites
    end

    subgraph IMU_G["IMU"]
        direction TB
        subgraph ACCEL["Accelerometer"]
            ax["ax_mps2"]
            ay["ay_mps2"]
            az["az_mps2"]
        end
        subgraph GYRO["Gyroscope (opt.)"]
            gx["gx_rad_s"]
            gy["gy_rad_s"]
            gz["gz_rad_s"]
        end
        subgraph MAG["Magnetometer (opt.)"]
            mx["mx_uT"]
            my["my_uT"]
            mz["mz_uT"]
        end
    end

    subgraph VEH["Vehicle I/O (opt.)"]
        ign["ignition"]
        odo["odometer_m"]
        spd_obd["speed_obd_mps"]
        volt["vehicle_voltage_v"]
        rpm_f["rpm"]
    end

    subgraph XTR["Extra (opt.)"]
        x_f["x_&lt;source&gt;_&lt;field&gt;"]
    end

    DT --- GNSS --- IMU_G --- VEH --- XTR

    style DT fill:#fff9c4,stroke:#f9a825
    style GNSS fill:#e8f5e9,stroke:#2e7d32
    style IMU_G fill:#e3f2fd,stroke:#1565c0
    style VEH fill:#fce4ec,stroke:#c62828
    style XTR fill:#f3e5f5,stroke:#6a1b9a
```

### 2.2 Mandatory Fields

Every Telemachus-compliant file MUST contain these columns:

| Column | Type | Unit | Source | Description |
|--------|------|------|--------|-------------|
| `ts` | datetime64[ns, UTC] | UTC | Device clock | Timestamp at IMU rate |
| `lat` | float64 | degrees WGS84 | GNSS | Latitude. NaN between GNSS ticks |
| `lon` | float64 | degrees WGS84 | GNSS | Longitude. NaN between GNSS ticks |
| `speed_mps` | float32 | m/s | GNSS Doppler | Ground speed. NaN between GNSS ticks |
| `ax_mps2` | float32 | m/s² | IMU accel | Longitudinal acceleration (+ = forward) |
| `ay_mps2` | float32 | m/s² | IMU accel | Lateral acceleration (+ = left) |
| `az_mps2` | float32 | m/s² | IMU accel | Vertical acceleration (~9.81 at rest if raw) |
| `device_id` | string | — | Config | Unique device identifier |
| `trip_id` | string | — | Config | Unique trip identifier |

### 2.3 Recommended Fields — GNSS Metadata

These fields SHOULD be present when the hardware provides them:

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `heading_deg` | float32 | degrees [0, 360) | Course over ground (COG). NaN when stationary |
| `altitude_gps_m` | float32 | m | GNSS altitude (NMEA GGA). Typical accuracy: 10–30 m |
| `hdop` | float32 | — (ratio) | Horizontal Dilution of Precision. < 2.0 = good |
| `h_accuracy_m` | float32 | m | Horizontal position accuracy (Android/smartphones). Complementary to hdop |
| `n_satellites` | int8 | — | Number of satellites used in fix. > 6 = reliable |

> **`hdop` vs `h_accuracy_m`**: Commercial GNSS devices (Teltonika, Danlaw)
> report `hdop` (dimensionless ratio). Smartphones (Android) report
> `h_accuracy_m` (68th percentile radius in meters). Both may coexist; a
> dataset typically has one or the other, rarely both.

### 2.4 Optional Fields — Extended IMU

Present only if the device has the corresponding sensor. Columns MUST be
absent or all-NaN when the sensor is not available — they MUST NOT be
filled with zeros.

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `gx_rad_s` | float32 | rad/s | Gyroscope X (roll rate) |
| `gy_rad_s` | float32 | rad/s | Gyroscope Y (pitch rate) |
| `gz_rad_s` | float32 | rad/s | Gyroscope Z (yaw rate) |
| `mx_uT` | float32 | µT | Magnetometer X |
| `my_uT` | float32 | µT | Magnetometer Y |
| `mz_uT` | float32 | µT | Magnetometer Z |

```mermaid
graph TD
    subgraph IMU["IMU Sensor Tiers"]
        T1["Tier 1: Accelerometer only\n(ax, ay, az)\nCommercial telematics devices"]
        T2["Tier 2: Accel + Gyro\n(+ gx, gy, gz)\nAEGIS, STRIDE, RS3"]
        T3["Tier 3: Accel + Gyro + Magneto\n(+ mx, my, mz)\nPVS, STRIDE (full)"]
    end

    T1 --> T2 --> T3

    style T1 fill:#ffecb3,stroke:#ff8f00
    style T2 fill:#c8e6c9,stroke:#2e7d32
    style T3 fill:#bbdefb,stroke:#1565c0
```

### 2.5 Optional Fields — Vehicle I/O

Raw vehicle bus data (CAN/OBD) when the device is connected to the
vehicle electrical system.

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `ignition` | bool | — | Vehicle ignition state (digital input) |
| `odometer_m` | float64 | m | Odometer reading (CAN/OBD) |
| `speed_obd_mps` | float32 | m/s | Vehicle speed from OBD PID 0x0D. Independent of GNSS speed |
| `vehicle_voltage_v` | float32 | V | External power source voltage (12 V / 24 V system). Key signal for carrier state detection |
| `rpm` | float32 | rev/min | Engine RPM (CAN/OBD PID 0x0C) |

> **Two speed fields**: `speed_mps` (GNSS, mandatory) and `speed_obd_mps`
> (OBD, optional) are intentionally separate. GPS speed degrades below
> ~5 km/h and requires a fix; OBD speed is accurate at all speeds but
> requires CAN wiring. The comparison GPS vs OBD is a quality indicator.

```mermaid
graph LR
    subgraph SPEED["Speed Sources"]
        GPS_S["speed_mps\n(GNSS Doppler)\nMandatory D0"]
        OBD_S["speed_obd_mps\n(OBD PID 0x0D)\nOptional D0 §3.4"]
    end

    GPS_S -- "compare" --> SQS["Signal Quality\nScore (D1)"]
    OBD_S -- "compare" --> SQS

    GPS_S -- "NaN at low speed" --> NOTE1["Degraded < 5 km/h\nNaN without fix"]
    OBD_S -- "accurate always" --> NOTE2["Requires CAN wiring\nNaN if no OBD"]

    style GPS_S fill:#e8f5e9,stroke:#2e7d32
    style OBD_S fill:#fce4ec,stroke:#c62828
    style SQS fill:#e3f2fd,stroke:#1565c0
```

### 2.6 Vendor-Specific Extra Fields

Telemachus files MAY contain additional columns not defined in this specification.
These columns MUST follow the naming convention:

```
x_<source>_<field>
```

Where `<source>` identifies the data provider or processing origin, and
`<field>` is a descriptive snake_case name.

**Examples:**

| Column | Source | Description |
|--------|--------|-------------|
| `x_pvs_road_surface` | PVS dataset | Road surface label (ground truth) |
| `x_pvs_temp_dashboard_c` | PVS dataset | Sensor temperature at dashboard placement |
| `x_stride_orientation_qw` | STRIDE dataset | Android orientation quaternion W |
| `x_stride_gravity_x_mps2` | STRIDE dataset | Android-derived gravity vector X |
| `x_teltonika_movement_status` | Teltonika | Firmware movement detection flag |
| `x_flespi_server_timestamp` | Flespi | Server-side receive timestamp |

**Rules:**
- Validators MUST ignore columns matching `x_*` (never reject them)
- Adapters SHOULD document their extra columns in the manifest
- Consumers MUST NOT assume any `x_*` column is present

### 2.7 Multi-Rate Convention

Telemachus files are timestamped at the **highest sensor rate** (typically
IMU rate, e.g. 10–100 Hz). Lower-rate columns (GNSS at 1 Hz) contain
NaN on rows where no measurement is available.

```mermaid
sequenceDiagram
    participant IMU as IMU (10 Hz)
    participant GPS as GNSS (1 Hz)
    participant D0 as D0 Row

    Note over IMU,D0: t = 0.0s
    IMU->>D0: ax=0.12, ay=0.03, az=9.81
    GPS->>D0: lat=49.33, lon=1.38, speed=5.2

    Note over IMU,D0: t = 0.1s
    IMU->>D0: ax=0.15, ay=-0.01, az=9.80
    GPS--xD0: NaN (no fix this tick)

    Note over IMU,D0: t = 0.2s
    IMU->>D0: ax=0.11, ay=0.02, az=9.82
    GPS--xD0: NaN

    Note over IMU,D0: ...

    Note over IMU,D0: t = 1.0s
    IMU->>D0: ax=0.13, ay=0.01, az=9.81
    GPS->>D0: lat=49.34, lon=1.38, speed=5.3
```

### 2.8 AccPeriod — Accelerometer Frame Reference

Commercial telematics devices may apply **firmware-side gravity
compensation**. The same accelerometer can output data in different
reference frames:

| Frame | At rest | Behaviour |
|-------|---------|-----------|
| `raw` | `az ~ 9.81 m/s²` (gravity present) | Unprocessed sensor output |
| `compensated` | `az ~ 0 m/s²` (gravity removed) | Firmware has subtracted gravity |
| `partial` | `az ~ epsilon`, `0 < abs(epsilon) < g` | Imperfect compensation, residual gravity vector |

The accelerometer frame is declared **at manifest level** (see SPEC-02
§3.7), not per-row. Each AccPeriod is a contiguous time range with a
coherent frame.

**Default**: if no AccPeriod is declared, consumers MUST assume `raw`.

```mermaid
graph TD
    subgraph FRAMES["Accelerometer Frame Types"]
        RAW["raw\n|a| at rest ≈ 9.81 m/s²\nGravity present in signal"]
        COMP["compensated\n|a| at rest ≈ 0 m/s²\nGravity removed by firmware"]
        PART["partial\n|a| at rest ≈ residual_g\n0 < residual < g\nImperfect compensation"]
    end

    RAW -- "firmware enables\ngravity filter" --> COMP
    RAW -- "firmware imperfect\ncalibration" --> PART

    subgraph EXAMPLES["Real-World Examples"]
        E1["AEGIS, PVS, STRIDE\n→ raw"]
        E2["Commercial device\nwith gravity filter ON\n→ compensated"]
        E3["Prototype device\nimperfect calibration\n→ partial (0.101 g residual)"]
    end

    RAW --- E1
    COMP --- E2
    PART --- E3

    style RAW fill:#e8f5e9,stroke:#2e7d32
    style COMP fill:#e3f2fd,stroke:#1565c0
    style PART fill:#fff3e0,stroke:#e65100
```

### 2.9 What D0 MUST NOT Contain

The following columns are **explicitly excluded** from D0:

| Column | Correct Layer | Reason |
|--------|--------------|--------|
| `road_type` | D1 | Requires map data |
| `speed_limit_kmh` | D1 | Requires map data |
| `altitude_dem_m` | D1 | Requires external DEM |
| `slope_pct` | D1 | Derived from DEM |
| `event` | D2 | Algorithmic output |
| `sqs_global` | D1 | Computed metric |
| `lat_matched` | D1 | Requires OSRM map matching |
| `carrier_state` | Manifest | Per-trip metadata, not per-row (see SPEC-02) |
| `is_vehicle_data` | Manifest | Derived from carrier_state |

---

## 3. D0 Validation Rules

A Telemachus file is valid if:

1. All mandatory columns (§2.2) are present with correct types
2. `ts` is monotonically increasing (strictly)
3. **Per AccPeriod** (SPEC-02 §3.7), `|a|` mean at rest matches the declared frame:
   - `raw`: ≈ 9.81 ± 1.0 m/s²
   - `compensated`: ≈ 0 ± 1.0 m/s²
   - `partial`: ≈ `residual_g` ± 0.05 g
4. `lat` / `lon` are within [-90, 90] / [-180, 180] when not NaN
5. No enrichment columns from §2.9 are present
6. All extra columns follow the `x_<source>_<field>` convention
7. `speed_mps` ≥ 0 when not NaN
8. Gyro/magneto columns are either all present or all absent (no partial group)

---

## 4. D1 — Cleaned & Contextualized Layer

D1 adds enrichment columns derived from external sources (maps, DEM) or
signal processing (interpolation, calibration). D1 preserves ALL D0
columns unchanged.

```mermaid
graph LR
    subgraph INPUT["D0 Input"]
        D0_GPS["lat, lon (NaN gaps)"]
        D0_IMU["ax, ay, az"]
        D0_SPD["speed_mps"]
    end

    subgraph STAGES["D1 Processing Stages"]
        S1["GPS Upsampling\n(linear/kinematic)"]
        S2["IMU Calibration\n([REDACTED_METHOD] [REDACTED_METHOD])"]
        S3["Map Matching\n(OSRM)"]
        S4["DEM Enrichment\n(SRTM/IGN)"]
        S5["Signal Quality\nScoring"]
    end

    subgraph OUTPUT["D1 Added Columns"]
        C1["interpolated (bool)"]
        C2["dist_m"]
        C3["lat_matched, lon_matched"]
        C4["road_type, speed_limit_kmh, urban"]
        C5["altitude_dem_m, slope_pct"]
        C6["sqs_global (0-1)"]
    end

    D0_GPS --> S1 --> C1
    D0_GPS --> S1 --> C2
    D0_GPS --> S3 --> C3
    S3 --> C4
    D0_GPS --> S4 --> C5
    D0_IMU --> S2
    D0_SPD --> S5 --> C6

    style INPUT fill:#e8f5e9,stroke:#2e7d32
    style STAGES fill:#e3f2fd,stroke:#1565c0
    style OUTPUT fill:#bbdefb,stroke:#1565c0
```

### 4.1 D1 Columns Added

| Column | Stage | Type | Description |
|--------|-------|------|-------------|
| `interpolated` | GPS Upsampling | bool | True if this row was interpolated (not a real GNSS fix) |
| `dist_m` | GPS Cleaning | float64 | Incremental haversine distance from previous fix |
| `lat_matched` | Map Matching | float64 | OSRM-snapped latitude |
| `lon_matched` | Map Matching | float64 | OSRM-snapped longitude |
| `road_type` | Road Context | string | OSM road classification |
| `speed_limit_kmh` | Road Context | float32 | Regulatory speed limit |
| `urban` | Road Context | bool | Urban zone flag |
| `altitude_dem_m` | DEM Enrichment | float32 | SRTM/IGN altitude |
| `slope_pct` | DEM Enrichment | float32 | Road grade (%) |
| `sqs_global` | Signal Quality | float32 | Score 0–1 (composite quality metric) |

---

## 5. D2 — Events & Situations Layer

D2 adds driving events and road classification detected from D1 signals.
D2 preserves ALL D0 + D1 columns unchanged.

```mermaid
graph TD
    subgraph DETECT["D2 Event Detection"]
        AX["ax_mps2\n(calibrated D1)"] --> BRAKE["HARSH_BRAKE\nax < -3.0 m/s²"]
        AX --> ACCEL["HARSH_ACCEL\nax > +2.5 m/s²"]
        AY["ay_mps2"] --> TURN["SHARP_TURN\nay > 5.0 m/s²"]
        AZ["az_mps2"] --> BUMP["SPEED_BUMP\nΔaz 3.0–5.0 m/s²"]
        AZ --> POTHOLE["POTHOLE\nΔaz > 5.0 m/s²"]
        SPD["speed_mps"] --> STOP["STOP\n< 0.3 m/s for ≥ 5s"]
    end

    subgraph CURVE["Curve Classification"]
        HEAD["heading_deg\n(D1 enriched)"] --> RADIUS["curve_radius_m"]
        RADIUS --> HAIRPIN["hairpin < 30m"]
        RADIUS --> SHARP["sharp 30–75m"]
        RADIUS --> MODERATE["moderate 75–200m"]
        RADIUS --> GENTLE["gentle > 200m"]
    end

    style DETECT fill:#fff3e0,stroke:#e65100
    style CURVE fill:#fce4ec,stroke:#c62828
```

### 5.1 D2 Columns Added

| Column | Type | Description |
|--------|------|-------------|
| `event` | string | Event type per row (empty if none) |
| `curve_radius_m` | float32 | Instantaneous curve radius |
| `curve_class` | string | hairpin / sharp / moderate / gentle / straight |

### 5.2 Event Types

| Code | Signal | Default Threshold | Category |
|------|--------|-------------------|----------|
| `HARSH_BRAKE` | ax | < -3.0 m/s² | Driving |
| `HARSH_ACCEL` | ax | > +2.5 m/s² | Driving |
| `SHARP_TURN` | gz or ay | > 0.3 rad/s or > 5.0 m/s² | Driving |
| `SPEED_BUMP` | az_delta | 3.0–5.0 m/s² | Infrastructure |
| `POTHOLE` | az_delta | > 5.0 m/s² | Infrastructure |
| `CURB` | ay + az | ay > 2.5 and az_delta > 3.0 | Infrastructure |
| `STOP` | speed | < 0.3 m/s for >= 5 s | Kinematic |

### 5.3 D3/D4 — Out of Scope

D3 (indicators, scoring) and D4 (fleet aggregation) are **application-level
concerns** outside the scope of this specification. Telemachus standardizes
the data format up to D2.

---

## 6. Hardware Mapping

### 6.1 Source Coverage Matrix

```mermaid
graph TD
    subgraph COMMERCIAL["Commercial Devices"]
        TELTO["Teltonika FMC880\n(Europe)"]
        TELTM["Teltonika FMM880\n(Americas)"]
        PROTO["Telematics Prototype\n(experimental)"]
    end

    subgraph RESEARCH["Research Platforms"]
        AEGIS["AEGIS\n(BeagleBone, Austria)"]
        PVS["PVS\n(MPU-9250 ×3, Brazil)"]
        STRIDE["STRIDE\n(POCO X2, Bangladesh)"]
    end

    subgraph SIM["Simulation"]
        RS3["RoadSimulator3\n(synthetic)"]
    end

    subgraph TIERS["Sensor Coverage"]
        T1["GPS + Accel"]
        T2["GPS + Accel + Gyro"]
        T3["GPS + Accel + Gyro + Magneto"]
        T4["GPS + Accel + OBD"]
    end

    TELTO --> T1
    TELTM --> T1
    PROTO --> T1
    AEGIS --> T4
    PVS --> T3
    STRIDE --> T3
    RS3 --> T2

    style COMMERCIAL fill:#fce4ec,stroke:#c62828
    style RESEARCH fill:#e8f5e9,stroke:#2e7d32
    style SIM fill:#e3f2fd,stroke:#1565c0
    style TIERS fill:#fff9c4,stroke:#f9a825
```

### 6.2 Detailed Column Mapping

#### Teltonika FMC880 / FMM880 (via Flespi)

| Flespi JSON Key | D0 Column | Conversion |
|-----------------|-----------|------------|
| `timestamp` | `ts` | epoch sec → UTC datetime |
| `position.latitude` | `lat` | direct (decimal degrees) |
| `position.longitude` | `lon` | direct |
| `position.speed` | `speed_mps` | km/h ÷ 3.6 |
| `position.direction` | `heading_deg` | direct (0–360°) |
| `position.altitude` | `altitude_gps_m` | direct (meters) |
| `position.hdop` | `hdop` | direct |
| `position.satellites` | `n_satellites` | direct |
| `x.acceleration` | `ax_mps2` | g × 9.80665 |
| `y.acceleration` | `ay_mps2` | g × 9.80665 |
| `z.acceleration` | `az_mps2` | g × 9.80665 |
| `engine.ignition.status` | `ignition` | direct (bool) |
| `external.powersource.voltage` | `vehicle_voltage_v` | direct (V) |
| `vehicle.mileage` | `odometer_m` | km × 1000 |
| `ident` | `device_id` | IMEI string |

#### AEGIS (Zenodo 820576, Austria)

| Raw CSV Column | D0 Column | Conversion |
|----------------|-----------|------------|
| `timestamp` (accelerations.csv) | `ts` | ISO string → UTC datetime |
| `x_value` (accelerations.csv) | `ax_mps2` | **G-force × 9.80665** |
| `y_value` | `ay_mps2` | G-force × 9.80665 |
| `z_value` | `az_mps2` | G-force × 9.80665 |
| `x_value` (gyroscopes.csv) | `gx_rad_s` | **deg/s × π/180** |
| `y_value` | `gy_rad_s` | deg/s × π/180 |
| `z_value` | `gz_rad_s` | deg/s × π/180 |
| `latitude` (positions.csv) | `lat` | **NMEA DDMM.MMMM → decimal degrees** |
| `longitude` | `lon` | NMEA → decimal degrees |
| `altitude` | `altitude_gps_m` | direct (meters) |
| `data` (obdData.csv, PID 0x0D) | `speed_obd_mps` | km/h ÷ 3.6 |
| `trip_id` | `trip_id` | direct |
| `beaglebone_id` (trips.csv) | `device_id` | lookup |

#### PVS (Kaggle, Curitiba)

| Raw CSV Column | D0 Column | Conversion |
|----------------|-----------|------------|
| `timestamp` | `ts` | Unix seconds → UTC datetime |
| `acc_x_{placement}` | `ax_mps2` | direct (already m/s²) |
| `acc_y_{placement}` | `ay_mps2` | direct |
| `acc_z_{placement}` | `az_mps2` | direct |
| `gyro_x_{placement}` | `gx_rad_s` | **deg/s × π/180** |
| `gyro_y_{placement}` | `gy_rad_s` | deg/s × π/180 |
| `gyro_z_{placement}` | `gz_rad_s` | deg/s × π/180 |
| `mag_x_{placement}` | `mx_uT` | direct (µT) |
| `mag_y_{placement}` | `my_uT` | direct |
| `mag_z_{placement}` | `mz_uT` | direct |
| `latitude` | `lat` | direct (decimal degrees) |
| `longitude` | `lon` | direct |
| `speed` | `speed_mps` | direct (already m/s) |
| `elevation` (GPS CSV) | `altitude_gps_m` | direct |
| `hdop` (GPS CSV) | `hdop` | direct |
| `satellites` (GPS CSV) | `n_satellites` | direct |

#### STRIDE (Figshare, Rajshahi)

| Raw CSV Column | D0 Column | Conversion |
|----------------|-----------|------------|
| `time` (TotalAcceleration.csv) | `ts` | **ns epoch → UTC datetime** |
| `x` (TotalAcceleration.csv) | `ax_mps2` | direct (already m/s²) |
| `y` | `ay_mps2` | direct |
| `z` | `az_mps2` | direct |
| `x` (Gyroscope.csv) | `gx_rad_s` | direct (already rad/s) |
| `y` | `gy_rad_s` | direct |
| `z` | `gz_rad_s` | direct |
| `x` (Magnetometer.csv) | `mx_uT` | direct (µT) |
| `y` | `my_uT` | direct |
| `z` | `mz_uT` | direct |
| `latitude` (Location.csv) | `lat` | direct (decimal degrees) |
| `longitude` | `lon` | direct |
| `speed` (Location.csv) | `speed_mps` | direct (already m/s) |
| `altitude` (Location.csv) | `altitude_gps_m` | direct |
| `bearing` (Location.csv) | `heading_deg` | direct (degrees) |
| `horizontalAccuracy` (Location.csv) | `h_accuracy_m` | direct (meters) |

#### RoadSimulator3 (Synthetic)

| RS3 Field | D0 Column | Conversion |
|-----------|-----------|------------|
| `timestamp` | `ts` | direct (10 Hz uniform UTC) |
| `lat`, `lon` | `lat`, `lon` | direct |
| `speed` | `speed_mps` | direct |
| `heading` | `heading_deg` | direct |
| `acc_x/y/z` | `ax/ay/az_mps2` | direct (includes gravity on az) |
| `gyro_x/y/z` | `gx/gy/gz_rad_s` | direct (NaN if disabled) |

> **Note:** RS3 also exports `road_type`, `event`, `target_speed` — these
> are **ground truth metadata** for validation, NOT part of D0. They should
> be stored as `x_rs3_*` extra columns or in a sidecar file.

---

## 7. Unit Conversion Reference

Adapters MUST convert raw device units to Telemachus canonical units:

| Quantity | D0 Unit | Common Raw Units | Conversion |
|----------|---------|-----------------|------------|
| Speed | m/s | km/h | ÷ 3.6 |
| Acceleration | m/s² | G-force | × 9.80665 |
| Gyroscope | rad/s | deg/s | × π / 180 |
| Magnetometer | µT | µT | (usually native) |
| GPS coordinates | decimal degrees | NMEA DDMM.MMMM | `DD + MM.MMMM / 60` |
| GPS coordinates | decimal degrees | decimal degrees | (no conversion) |
| Odometer | m | km | × 1000 |
| Voltage | V | V | (no conversion) |
| Timestamp | datetime64[ns, UTC] | epoch seconds | × 1e9 + to_datetime |
| Timestamp | datetime64[ns, UTC] | epoch nanoseconds | to_datetime |
| Timestamp | datetime64[ns, UTC] | ISO 8601 string | parse + ensure UTC |

---

## 8. Python API — Sensor Introspection

The `telemachus-py` library provides introspection helpers for consumers
to discover what data is available without loading the full dataset:

### 8.1 Manifest-Level (fast, no data loaded)

```python
ds = tele.Dataset.from_manifest("manifest.yaml")
ds.declared_sensors()    # → {'gps': {'rate_hz': 1}, 'accelerometer': {...}, ...}
ds.has_declared_gyro()   # → True / False
ds.acc_frame()           # → "raw" | "compensated" | "partial"
```

### 8.2 Data-Level (loads parquet, checks actual content)

```python
df = tele.read("manifest.yaml")
tele.has_gps(df)         # → True if lat, lon, speed_mps have non-NaN values
tele.has_imu(df)         # → True if ax, ay, az have non-NaN values
tele.has_gyro(df)        # → True if gx, gy, gz present and non-NaN
tele.has_magneto(df)     # → True if mx, my, mz present and non-NaN
tele.has_obd(df)         # → True if speed_obd_mps or rpm present and non-NaN
tele.sensor_profile(df)  # → "gps+imu+gyro+magneto" or "gps+imu" etc.
tele.is_gps_only(df)     # → GPS but no IMU
tele.is_full_imu(df)     # → accel + gyro available
```

---

## 9. References

- **SPEC-02**: Dataset Manifest — canonical file-level metadata
- **SPEC-03**: Adapters & Validation — tooling and conformance testing
- **Superseded RFCs**: RFC-0001 (Core v0.2), RFC-0004 (Extended FieldGroups), RFC-0013 (Telemachus Device Format v0.7)

### Dataset References

| Dataset | DOI / URL | License |
|---------|-----------|---------|
| AEGIS | Zenodo 820576 | CC-BY-4.0 |
| PVS | Kaggle (Curitiba) | CC-BY-NC-ND-4.0 |
| STRIDE | Figshare 25460755 | CC-BY-4.0 |
| UAH-DriveSet | Universidad de Alcala | Academic |

---

End of SPEC-01.
