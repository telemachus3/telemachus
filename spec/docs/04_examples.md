# Examples

This document aligns with Telemachus v0.2 and references RFC-0001 and RFC-0003.

Examples are essential for understanding how to implement and utilize the Telemachus Core schema effectively. They provide concrete illustrations of how data should be structured, making it easier for developers and analysts to interpret, validate, and integrate telemetry data consistently across different systems and applications.

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
  "powertrain": {
    "rpm": 2450,
    "odometer_km": 10532.4,
    "throttle_pct": 34.0,
    "coolant_temp_c": 92.0,
    "battery_voltage_v": 13.8
  },
  "events": [
    {
      "event_id": "EVT-001",
      "type": "harsh_brake",
      "severity": "high",
      "start": "2025-01-01T12:00:10Z",
      "end": "2025-01-01T12:00:12Z",
      "metadata": {"decel_ms2": -5.4}
    }
  ],
  "context": {
    "topography": {"slope_deg": -3.0, "surface_type": "asphalt"},
    "weather": {"temp_c": 7.5, "precip_mm": 0.0},
    "environmental_impact": {"co2_emission_gpkm": 120, "noise_db": 65},
    "urban": {"road_type": "city_street", "traffic_density": "moderate"},
    "safety": {"lane_departure_warnings": 2, "collision_alerts": 1}
  },
  "energy": {
    "fuel_pct": 67.5,
    "fuel_l": 45.2,
    "fuel_rate_lph": 2.1,
    "consumed_kwh": 12.3,
    "recovered_kwh": 1.2,
    "state_of_charge_pct": 85.0,
    "charging_status": "discharging",
    "energy_source": "hybrid"
  },
  "source": {
    "provider": "geotab",
    "device_id": "DEVICE-9876",
    "ingest_timestamp": "2025-01-01T12:00:05Z",
    "schema_version": "0.2"
  }
}
```

### Explanation of Field Groups

- **timestamp** and **vehicle_id**: Identify when the record was captured and which vehicle it pertains to.
- **position**: Provides the geospatial fix including latitude, longitude, altitude, and heading.
- **motion**: Describes the vehicle's movement with speed and bearing.
- **quality**: Indicates GNSS fix quality metrics to assess data reliability.
- **imu**: Contains inertial measurement unit data such as acceleration, rotation rates, magnetometer readings, and sample rate.
- **powertrain**: Captures engine and CAN bus telemetry including RPM, odometer, throttle position, coolant temperature, and battery voltage. This replaces the former `engine` group.
- **events**: Lists detected driving events like harsh braking, with severity and timing metadata.
- **context**: Adds environmental and road conditions such as topography and weather. It now also supports environmental, urban, and safety extensions per RFC-0004.
- **energy**: Represents optional extended FieldGroups related to vehicle energy management, including fuel level and consumption, battery state of charge, charging status, and energy source type (see RFC-0004).
- **source**: Identifies the data provider, device ID, ingest timestamp, and schema version for traceability.

This schema and its examples are designed to be validated against formal validation rules as specified in RFC-0007 to ensure data quality and consistency.

---

## Minimal Record Example

A minimal valid Telemachus Core record includes only the required fields: `timestamp`, `vehicle_id`, and `position` with latitude and longitude.

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "vehicle_id": "FLEET-123",
  "position": {
    "lat": 48.8566,
    "lon": 2.3522
  },
  "source": {
    "schema_version": "0.2"
  }
}
```

This minimal record is useful for basic location tracking scenarios where additional telemetry data is not available or necessary.

---

## Dataset Example

Telemetry data is often collected as a series of records representing sequential time points. Below is an example dataset containing multiple Telemachus Core records in an array.

```json
[
  {
    "timestamp": "2025-01-01T12:00:00Z",
    "vehicle_id": "FLEET-123",
    "position": {"lat": 48.8566, "lon": 2.3522},
    "motion": {"speed_kph": 50.0, "bearing_deg": 180.0}
  },
  {
    "timestamp": "2025-01-01T12:00:10Z",
    "vehicle_id": "FLEET-123",
    "position": {"lat": 48.8570, "lon": 2.3525},
    "motion": {"speed_kph": 52.4, "bearing_deg": 182.0},
    "powertrain": {"rpm": 2400}
  },
  {
    "timestamp": "2025-01-01T12:00:20Z",
    "vehicle_id": "FLEET-123",
    "position": {"lat": 48.8575, "lon": 2.3530},
    "quality": {"hdop": 0.9, "num_satellites": 11}
  },
  {
    "timestamp": "2025-01-01T12:00:30Z",
    "vehicle_id": "FLEET-123",
    "position": {"lat": 48.8580, "lon": 2.3535},
    "powertrain": {
      "rpm": 2500,
      "odometer_km": 10535.0,
      "throttle_pct": 40.0,
      "coolant_temp_c": 90.0,
      "battery_voltage_v": 13.7
    },
    "energy": {
      "fuel_pct": 65.0,
      "fuel_l": 44.0,
      "fuel_rate_lph": 2.0,
      "consumed_kwh": 13.0,
      "recovered_kwh": 1.5,
      "state_of_charge_pct": 80.0,
      "charging_status": "charging",
      "energy_source": "hybrid"
    }
  }
]
```

This dataset format is ideal for applications such as:

- **Simulation**: Feeding time-series telemetry into vehicle simulators.
- **Fleet Analysis**: Monitoring vehicle behavior over time for diagnostics or optimization.
- **Data Visualization**: Plotting trajectories and sensor data trends.

Note that this dataset format aligns with RS3 integration protocols (RFC-0009) and can be accompanied by a dataset manifest as described in RFC-0003 for enhanced data management.

---

## Best Practices

- Use ISO-8601 format for all timestamps to ensure consistency and interoperability.
- Always specify units for all measurements (e.g., meters, degrees, seconds) to avoid ambiguity.
- Include only required fields for minimal records; add optional fields as available to enrich data quality.
- Leverage the `context` field to provide environmental and situational information that can enhance analysis.
- Maintain clear and consistent `source` metadata for data provenance and auditing.
- Validate data quality fields to assess the reliability of GNSS and sensor measurements before use.

---

## Schema Governance

Examples provided in this document are verified under the Telemachus validation framework as specified in RFC-0007, ensuring compliance with schema rules and data integrity. The schema and its examples evolve according to governance processes outlined in RFC-0011, enabling controlled updates and community-driven improvements.

All examples conform to the `telemachus_core_v0.2.json` schema.