# Telemachus Core Specification v0.1-alpha

## Overview

The Telemachus Core v0.1-alpha schema defines a standard structure for vehicle telemetry data. It covers various data domains including GNSS positioning, motion parameters, data quality metrics, inertial measurement unit (IMU) readings, engine and CAN bus information, event logging, contextual metadata, and source identification.

## Required Fields

- `timestamp`: The ISO 8601 timestamp of the data sample.
- `vehicle_id`: Unique identifier for the vehicle.
- `position.lat`: Latitude coordinate in decimal degrees.
- `position.lon`: Longitude coordinate in decimal degrees.

## Field Groups

- **GNSS**  
  - `lat`  
  - `lon`  
  - `altitude_m`  
  - `heading_deg`

- **Motion**  
  - `speed_kph`  
  - `bearing_deg`

- **Quality**  
  - `hdop`  
  - `vdop`  
  - `pdop`  
  - `num_satellites`  
  - `fix_type`

- **IMU**  
  - `accel_x`  
  - `accel_y`  
  - `accel_z`  
  - `gyro_x`  
  - `gyro_y`  
  - `gyro_z`  
  - `mag_x`  
  - `mag_y`  
  - `mag_z`  
  - `sample_rate_hz`

- **Engine/CAN**  
  - `rpm`  
  - `odometer_km`  
  - `fuel_pct`  
  - `fuel_l`  
  - `fuel_rate_lph`  
  - `throttle_pct`  
  - `engine_temp_c`  
  - `battery_voltage_v`

- **Events**  
  An array of objects containing:  
  - `type`  
  - `severity`  
  - `start`  
  - `end`  
  - `metadata`

- **Context**  
  - `topography`  
  - `weather`  
  - Extensible for additional contextual information

- **Source metadata**  
  - `provider`  
  - `device_id`  
  - `ingest_timestamp`

## JSON Schema Link

The JSON Schema for Telemachus Core v0.1-alpha is available at:  
`schemas/telemachus.schema.json`
