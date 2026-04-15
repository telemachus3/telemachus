# Concepts

The four ideas you need to grok to read Telemachus data correctly.

## D0 → D1 → D2 — the layered model

| Layer | Name | Input | Output |
|-------|------|-------|--------|
| **D0** | Device | Hardware | Raw parquet — only what the device measures |
| **D1** | Cleaned & Contextualised | D0 | Enriched D0 + map matching, DEM, IMU calibration, signal quality |
| **D2** | Events & Situations | D1 | D1 + event column + event table (harsh brake, pothole, curve, …) |

The Telemachus spec is **normative on D0** (RFC-0013). D1 and D2
column contracts are documented in RFC-0013 §4 but their *algorithms*
are intentionally out of scope — different consumers can compute D1/D2
differently as long as they emit conformant columns.

**Rule of thumb**: a column derived from external data (maps, DEM,
algorithm output) belongs to D1 or higher, never D0.

## Multi-rate IMU vs GNSS

Most devices stream IMU at 10 Hz and GNSS at 1 Hz. D0 is timestamped
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
RFC-0013 §3.6 for the full normative definition.

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
RFC-0013 §3.7 for the decision tree.

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
