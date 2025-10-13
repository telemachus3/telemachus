# Telemachus Core Specification v0.2

## Overview

The Telemachus Core v0.2 schema defines the foundational structure of the Telemachus standard, designed to ensure interoperability between simulation, telematics, and open mobility datasets. This core schema establishes a common framework for representing vehicle telemetry data, facilitating consistent data exchange and integration across diverse applications and platforms.

This core schema is defined and detailed in [RFC-0001: Telemachus Core Specification v0.2](../rfcs/RFC-0001-telemachus-core-0.2.md), which provides the formal specification and rationale behind the schema design.

### Version Alignment

This document follows the specifications outlined in RFC-0001 and corresponds to Telemachus Specification version 0.2, ensuring alignment between the schema definition and the broader Telemachus ecosystem.

## Required Fields

- `timestamp`: The ISO 8601 timestamp of the data sample.
- `vehicle_id`: Unique identifier for the vehicle.
- `position.lat`: Latitude coordinate in decimal degrees.
- `position.lon`: Longitude coordinate in decimal degrees.

## Field Groups

- **GNSS**
  - `lat`: Latitude coordinate in decimal degrees. Required. Must follow the WGS84 coordinate reference system.
  - `lon`: Longitude coordinate in decimal degrees. Required. Must follow the WGS84 coordinate reference system.
  - `altitude_m`: Altitude above mean sea level in meters. Optional.
  - `heading_deg`: Heading (direction of travel) in degrees, where 0 is North. Optional.

- **Motion**
  - `speed_kph`: Speed of the vehicle in kilometers per hour (km/h). Optional.
  - `bearing_deg`: Bearing in degrees, representing the direction of movement. Optional.

- **Quality**
  - `hdop`: Horizontal Dilution of Precision, unitless. Indicates GNSS horizontal accuracy. Optional.
  - `vdop`: Vertical Dilution of Precision, unitless. Indicates GNSS vertical accuracy. Optional.
  - `pdop`: Position Dilution of Precision, unitless. Indicates overall GNSS accuracy. Optional.
  - `num_satellites`: Number of GNSS satellites used for the fix. Optional.
  - `fix_type`: Type of GNSS fix (e.g., "none", "2d", "3d", "dgps", "rtk"). Optional.

- **IMU**
  - `accel_x`, `accel_y`, `accel_z`: Acceleration along X, Y, Z axes in meters per second squared (m/s²). Optional.
  - `gyro_x`, `gyro_y`, `gyro_z`: Angular velocity around X, Y, Z axes in radians per second (rad/s). Optional.
  - `mag_x`, `mag_y`, `mag_z`: Magnetic field along X, Y, Z axes in microteslas (µT). Optional.
  - `sample_rate_hz`: IMU sample rate in Hertz (Hz). Optional.

- **Powertrain & Electrical**
  - `rpm`: Engine revolutions per minute. Optional.
  - `odometer_km`: Total distance traveled by the vehicle in kilometers. Optional.
  - `fuel_pct`: Remaining fuel as a percentage (0-100). Optional.
  - `fuel_l`: Remaining fuel in liters. Optional.
  - `fuel_rate_lph`: Instantaneous fuel consumption rate in liters per hour. Optional.
  - `throttle_pct`: Throttle position as a percentage (0-100). Optional.
  - `engine_temp_c`: Engine temperature in degrees Celsius. Optional.
  - `battery_voltage_v`: Battery voltage in volts. Optional.

- **Events**
  - An array of objects, each representing a detected event:
    - `type`: Event type (e.g., "harsh_brake", "accident"). Required.
    - `severity`: Event severity (e.g., "low", "medium", "high"). Optional.
    - `start`: ISO 8601 timestamp when the event started. Optional.
    - `end`: ISO 8601 timestamp when the event ended. Optional.
    - `metadata`: Arbitrary key-value pairs with event-specific details. Optional.
  - Example:  
    ```json
    {
      "type": "harsh_brake",
      "severity": "high",
      "start": "2024-01-01T12:00:05Z",
      "end": "2024-01-01T12:00:06Z",
      "metadata": {"deceleration_mps2": 8.5}
    }
    ```

- **Context**
  - Additional contextual metadata, extensible to support new domains.
    - `topography`: Road topography or grade (e.g., "flat", "uphill", "downhill"). Optional.
    - `weather`: Weather conditions (e.g., "clear", "rain", "snow"). Optional.
    - Extensible fields: Arbitrary additional context such as:
      - `road_genome`: Road attributes (surface type, lane count, etc.).
      - `emissions`: Estimated or measured emissions data.
      - Any other relevant contextual data.

- **Source metadata**
  - Information about data origin for traceability and audit:
    - `provider`: Name or identifier of the data provider.
    - `device_id`: Unique identifier of the data collection device or sensor.
    - `ingest_timestamp`: ISO 8601 timestamp when the record was ingested or received by the system.

- **Extended FieldGroups (RFC-0004)**
  - The core schema can be optionally complemented by extended field groups as defined in RFC-0004, which provide additional structure for energy and diagnostics data to support advanced use cases.

## JSON Schema Link

The JSON Schema for Telemachus Core v0.2 is available at:  
`https://telemachus3.github.io/telemachus-spec/schemas/telemachus_core_v0.2.json`


## Example Record

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "vehicle_id": "ABC123",
  "position": {
    "lat": 48.8566,
    "lon": 2.3522,
    "altitude_m": 35.2,
    "heading_deg": 90.0
  },
  "motion": {
    "speed_kph": 50.5,
    "bearing_deg": 91.2
  },
  "quality": {
    "hdop": 0.9,
    "vdop": 1.2,
    "pdop": 1.6,
    "num_satellites": 10,
    "fix_type": "3d"
  },
  "imu": {
    "accel_x": 0.01,
    "accel_y": -0.02,
    "accel_z": 9.81,
    "gyro_x": 0.001,
    "gyro_y": -0.002,
    "gyro_z": 0.0005,
    "mag_x": 35.6,
    "mag_y": -12.7,
    "mag_z": 47.2,
    "sample_rate_hz": 100
  },
  "engine": {
    "rpm": 2200,
    "odometer_km": 15023.7,
    "fuel_pct": 68.5,
    "fuel_l": 32.1,
    "fuel_rate_lph": 7.2,
    "throttle_pct": 15.0,
    "engine_temp_c": 89.5,
    "battery_voltage_v": 13.8
  },
  "events": [
    {
      "type": "harsh_brake",
      "severity": "high",
      "start": "2024-01-01T12:00:05Z",
      "end": "2024-01-01T12:00:06Z",
      "metadata": {
        "deceleration_mps2": 8.5
      }
    }
  ],
  "context": {
    "topography": "downhill",
    "weather": "rain",
    "road_genome": {
      "surface_type": "asphalt",
      "lanes": 2
    },
    "emissions": {
      "co2_g_km": 120
    }
  },
  "source": {
    "provider": "FleetCorp",
    "device_id": "DEV-0012345",
    "ingest_timestamp": "2024-01-01T12:00:01Z"
  }
}
```

## Schema Governance

The Telemachus Core schema evolves through a community-driven process based on RFC proposals. Changes, enhancements, and extensions are proposed via RFC documents and undergo review, discussion, and validation testing as outlined in [RFC-0011: Telemachus Schema Validation and Governance](../rfcs/RFC-0011-telemachus-schema-validation.md). This process ensures that the core schema remains robust, interoperable, and responsive to emerging requirements in the vehicle telemetry domain.
