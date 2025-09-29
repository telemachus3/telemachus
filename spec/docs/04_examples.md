


# Examples

This page provides a complete example of a Telemachus Core record using **GNSS**, **Motion**, **Quality**, **IMU**, **Engine/CAN**, **Events**, **Context**, and **Source** fields.

---

## Full JSON Example

Below is a comprehensive example JSON record that demonstrates all major field groups in the Telemachus Core schema.

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "vehicle_id": "FLEET-123",
  "position": {
    "lat": 48.8566,
    "lon": 2.3522,
    "altitude_m": 35.0,
    "heading_deg": 180.0
  },
  "motion": {
    "speed_kph": 52.4,
    "bearing_deg": 182.0
  },
  "quality": {
    "hdop": 0.9,
    "vdop": 1.2,
    "pdop": 1.5,
    "num_satellites": 12,
    "fix_type": "3d"
  },
  "imu": {
    "accel": {"x_ms2": 0.1, "y_ms2": 0.0, "z_ms2": 9.81},
    "gyro": {"x_rads": 0.0, "y_rads": 0.01, "z_rads": 0.02},
    "mag": {"x_ut": 25.3, "y_ut": -5.1, "z_ut": 43.2},
    "sample_rate_hz": 100
  },
  "engine": {
    "rpm": 2450,
    "odometer_km": 10532.4,
    "fuel_pct": 67.5,
    "fuel_l": 45.2,
    "fuel_rate_lph": 2.1,
    "throttle_pct": 34.0,
    "engine_temp_c": 92.0,
    "battery_voltage_v": 13.8
  },
  "events": [
    {
      "type": "harsh_brake",
      "severity": "high",
      "start": "2025-01-01T12:00:10Z",
      "end": "2025-01-01T12:00:12Z",
      "metadata": {"decel_ms2": -5.4}
    }
  ],
  "context": {
    "topography": {"slope_deg": -3.0, "surface_type": "asphalt"},
    "weather": {"temp_c": 7.5, "precip_mm": 0.0}
  },
  "source": {
    "provider": "geotab",
    "device_id": "DEVICE-9876",
    "ingest_timestamp": "2025-01-01T12:00:05Z"
  }
}
```

---

## Field Group Explanations

- **GNSS/Position**: `lat`, `lon`, `altitude_m`, and `heading_deg` give the geospatial fix and orientation.
- **Motion**: Includes `speed_kph` and `bearing_deg` (direction of movement).
- **Quality**: GNSS fix quality metrics such as `hdop`, `vdop`, `pdop`, satellite count, and fix type.
- **IMU**: Inertial sensors: acceleration, gyroscope, magnetometer, and sample rate.
- **Engine/CAN**: Engine telemetry such as RPM, odometer, fuel, throttle, temperature, and battery voltage.
- **Events**: List of detected events (e.g., harsh braking) with metadata.
- **Context**: Environmental and road context (e.g., topography, weather).
- **Source**: Data provider/device, device ID, and ingest timestamp.

---

## Notes
- Values are illustrative only.
- All groups (GNSS, Motion, IMU, CAN, etc.) are optional except `timestamp`, `vehicle_id`, and `position.lat/lon`.