# Concepts

The five ideas you need to grok to read Telemachus data correctly.

## Telemachus — functional groups

Telemachus is a **flat parquet** (the schema is columnar, not nested), but
mentally it splits into five functional groups. Knowing these groups
makes it much easier to remember why each column is there.

```
Telemachus = datetime       ts
   + GPS            lat, lon, speed_mps, heading_deg,
                    altitude_gps_m, hdop, n_satellites
   + IMU
       ├── accel    ax_mps2, ay_mps2, az_mps2
       ├── gyro     gx_rad_s, gy_rad_s, gz_rad_s   (optional)
       └── magneto  mx_uT,    my_uT,    mz_uT      (optional)
   + OBD / CAN      ignition, odometer_m, rpm,
                    speed_obd_mps, fuel_*, …       (optional)
   + extra          x_<source>_<field>             (vendor-specific)
```

| Group | What it tells you | Rate (typical) |
|-------|-------------------|----------------|
| **datetime** | *When* the sample was captured | IMU rate (10 Hz) |
| **GPS** | *Where* the vehicle is and how fast | 1 Hz (NaN between fixes) |
| **IMU** | *How* the vehicle moves (acc/rot/field) | 10–100 Hz |
| **OBD/CAN** | *What the vehicle reports* (bus data) | 1 Hz (varies) |
| **extra** | Anything vendor-specific that doesn't fit the above | varies |

!!! note "Why flat columns, not nested structs?"
    Parquet handles flat columns best (projection pushdown, fast
    scans). Nesting `imu.accel.x_mps2` looks tidy but costs perf and
    tooling compatibility. The *mental model* is nested; the *schema*
    is flat.

### Vendor-specific `extra` fields

When a vendor exposes a field that has no standard Telemachus
equivalent (a proprietary counter, a device-internal flag, …), use
the **`x_<source>_<field>`** naming convention:

| Column | Meaning |
|--------|---------|
| `x_teltonika_ext_voltage_v` | Teltonika external power voltage reading |
| `x_geotab_geofence_id` | Geotab-specific geofence identifier |
| `x_danlaw_codec_id` | Danlaw firmware codec tag |

The `x_` prefix signals "not part of the normative Telemachus contract,
consumer may safely ignore it". The `<source>` segment keeps names
unambiguous across datasets that merge multiple vendors.

## Telemachus record format — the layered model

| Layer | Name | Input | Output |
|-------|------|-------|--------|
| **Telemachus** | Device | Hardware | Raw parquet — only what the device measures |
| **enriched** | Cleaned & Contextualised | Telemachus | Enriched Telemachus + map matching, DEM, IMU calibration, signal quality |
| **events layer** | Events & Situations | enriched | enriched + event column + event table (harsh brake, pothole, curve, …) |

The Telemachus spec is **normative on Telemachus** (SPEC-01). enriched and events layer
column contracts are documented in SPEC-01 §4 but their *algorithms*
are intentionally out of scope — different consumers can compute enriched/events layer
differently as long as they emit conformant columns.

**Rule of thumb**: a column derived from external data (maps, DEM,
algorithm output) belongs to enriched format or higher, never Telemachus.

## Multi-rate IMU vs GNSS

Most devices stream IMU at 10 Hz and GNSS at 1 Hz. Telemachus is timestamped
at the **IMU rate**, with GNSS columns containing `NaN` between fixes:

```
ts                    lat      lon       speed_mps  ax_mps2  ay_mps2  az_mps2
2025-01-01T08:00:00.0 49.3347  1.3830    5.2        0.12     0.03     9.81
2025-01-01T08:00:00.1 NaN      NaN       NaN        0.15    -0.01     9.80
2025-01-01T08:00:00.2 NaN      NaN       NaN        0.11     0.02     9.82
…
2025-01-01T08:00:01.0 49.3348  1.3831    5.3        0.13     0.01     9.81
```

When computing GNSS-only metrics (distance, average speed), drop NaNs
explicitly. When computing IMU-only metrics (jerk, vibration), use all
rows.

The manifest `sensors.{gps,accelerometer}.rate_hz` declares the
expected rates so consumers can pre-allocate buffers and pick
interpolation strategies.

## AccPeriod — the accelerometer frame

The same physical accelerometer can output data in different
**reference frames** depending on firmware state:

| Frame | At rest | Behaviour |
|-------|---------|-----------|
| `raw` | `\|a\|` ≈ 9.81 m/s² | Unprocessed sensor output |
| `compensated` | `\|a\|` ≈ 0 m/s² | Firmware has subtracted gravity |
| `partial` | `0 < \|a\| < g` | Imperfect compensation |

This matters because downstream stages (IMU calibration, event
detection) need to know whether gravity is in the signal.

The manifest declares one or more `acc_periods` segments — each a
contiguous time range with a coherent frame:

```yaml
acc_periods:
  - start: 2025-01-01T00:00:00Z
    end:   2025-03-15T12:00:00Z
    frame: compensated
    detection_method: empirical
  - start: 2025-03-15T12:00:01Z
    end:   present
    frame: raw
    detection_method: profile_change
```

Default if absent: a single implicit period with `frame: "raw"`. See
SPEC-01 §3.6 for the full normative definition.

## CarrierState — is this trip real driving?

A telematics device records data continuously, but **not all of that
data comes from a real driving context**. A device left on a workshop
bench, manipulated by hand during testing, or temporarily unplugged
still emits messages.

The trip-level `carrier_state` classifies each trip into one of six
contexts:

| State | Description | Vehicle? | Use for analytics? |
|-------|-------------|----------|---------------------|
| `mounted_driving` | Installed in vehicle, vehicle in motion | Yes | Yes |
| `mounted_idle` | Installed, vehicle stationary | Yes | Yes (ZUPT) |
| `unplugged` | External power lost | Unknown | Optional |
| `desk` | Stable surface, no vehicle context | No | No |
| `handheld` | Being moved by hand | No | No |
| `unknown` | Insufficient signals | Unknown | No |

Classification combines four signals: external power voltage, GPS
speed, accelerometer norm variance, GPS position drift. See
SPEC-01 §3.7 for the decision tree.

In the manifest, declare them via `trip_carrier_states`:

```yaml
trip_carrier_states:
  - trip_id: "T20250410_1053_001"
    carrier_state: "mounted_driving"
    confidence: "high"
```

Downstream stages MUST filter on `is_vehicle_data == True` (i.e.
`carrier_state ∈ {mounted_driving, mounted_idle}`) for any analytics
that assume vehicle context.
