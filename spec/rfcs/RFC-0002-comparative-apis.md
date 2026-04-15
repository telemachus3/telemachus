---
RFC: 0002
Title: Comparative Telematics API Formats
Version: 0.1-draft
Status: Draft
Author: Sébastien Edet
Date: 2025-10-11
Project: Telemachus Specification
---

## Summary

This RFC presents a comparative analysis of major industrial telematics data formats — Webfleet (TomTom), Samsara, Geotab, and Teltonika — against the Telemachus v0.1 schema. Building on RFC-0001 (Telemachus Core 0.2) and the Telemachus Spec v0.1, it extends the core model with industrial “FieldGroups” such as engine, fuel, odometer, diagnostics, and energy. The RFC identifies structural similarities, divergences, and normalization opportunities to guide the development of Telemachus v0.2 and beyond. The goal is to define a unified, interoperable, and extensible data model that bridges industrial and open telemetry standards.

---

## 1. Purpose

This RFC provides a comprehensive comparative analysis of major industrial telematics data formats—**Webfleet (TomTom)**, **Samsara**, **Geotab**, and **Teltonika**—against the **Telemachus v0.1 schema**. The objective is to identify convergences, divergences, and essential structural fields to guide the design of a unified telematics data model for future Telemachus versions (v0.2 and v1.0). This work builds on RFC-0001 (Telemachus Core 0.2) and extends it with industrial “FieldGroups” such as engine, fuel, odometer, diagnostics, and energy, providing a bridge between open and industrial telematics standards.

---

## 2. Scope

- Emphasis on **vehicle telemetry and geospatial data** (timestamp, GNSS position, speed, heading, engine state).  
- Preliminary harmonisation of **engine, fuel, odometer, and diagnostic** data FieldGroups.  
- IMU and acceleration data from Telemachus Core are excluded, as industrial APIs typically do not expose raw inertial data.  
- Excludes authentication, rate limiting, webhook handling, and endpoint-specific logic.

---

## 3. Sources and References

| Provider             | Documentation                                                                 | Interface Type | Primary Format       |
|----------------------|-------------------------------------------------------------------------------|----------------|----------------------|
| **Webfleet (TomTom)** | [Webfleet.connect API](https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html) | REST / XML     | XML / JSON           |
| **Samsara**          | [Developer Portal](https://developers.samsara.com/reference/overview)         | REST v2        | JSON                 |
| **Geotab**           | [MyGeotab SDK](https://developers.geotab.com/myGeotab/introduction/)           | JSON-RPC       | JSON                 |
| **Teltonika**        | [Codec Protocols](https://wiki.teltonika-gps.com/view/Codec)                   | TCP / UDP binary | Binary (Codec8 / Codec8E) |
| **Telemachus**       | [Spec v0.1](https://github.com/telemachus3/telemachus-spec)                    | Open format    | JSON                 |

---

## 4. Core Data Model Comparison

| FieldGroup           | Telemachus key        | Samsara           | Webfleet                | Geotab           | Teltonika               |
|----------------------|-----------------------|-------------------|-------------------------|------------------|-------------------------|
| Timestamp            | `time`                | `time`            | `gpstime`               | `dateTime`       | Field 2 (timestamp)     |
| Latitude             | `position.lat`        | `latitude`        | `lat`                   | `latitude`       | Field 3                 |
| Longitude            | `position.lon`        | `longitude`       | `lon`                   | `longitude`      | Field 4                 |
| Speed (km/h)         | `speed.kmh`           | `speed`           | `speed`                 | `speed`          | AVL ID 1                |
| Heading (°)          | `heading.deg`         | `bearingDeg`      | `heading`               | `bearing`        | AVL ID 13               |
| Altitude (m)         | `altitude.m`          | `altitude`        | —                       | `altitude`       | AVL ID 22               |
| Ignition             | `engine.status`       | `engineState`     | `ignition`              | `ignition`       | AVL ID 239              |
| VIN                  | `vehicle.vin`         | `vin`             | `vehicleIdentificationNumber` | `vin`       | —                       |
| Odometer (km)        | `odometer.km`         | `odometerMeters`  | `mileage`               | `odometer`       | AVL ID 16               |
| Fuel Level (%)       | `fuel.level_percent`  | `fuelPerc`        | `fuelLevel`             | `fuelLevel`      | AVL ID 9                |
| DTC Codes            | `diagnostics.dtc`     | `faultCodes`      | —                       | `faultData`      | I/O ID 70–72            |

---

## 5. Alignment and Divergences

### 5.1 Timestamp and Position

- All providers use ISO 8601 or epoch timestamps; Telemachus uses ISO 8601 for clarity and interoperability.  
- Latitude and longitude keys vary but represent the same data. Telemachus nests these under `position` for semantic clarity.

### 5.2 Speed and Heading

- Speed is consistently in km/h across providers, except Teltonika which reports raw AVL data requiring conversion.  
- Heading is expressed in degrees; Samsara and Geotab use `bearing` or `bearingDeg`.

### 5.3 Engine and Vehicle State

- Ignition or engine state is represented with varying keys and value types (boolean, string states). Telemachus normalises this as `engine.status` with enumerated states (`on`, `off`, `unknown`).  
- VIN is universally supported except Teltonika, which lacks this field in raw data.

### 5.4 Odometer and Fuel

- Odometer readings differ in units (meters vs. kilometers); Telemachus standardises on kilometers.  
- Fuel level is consistently a percentage. Some providers omit or report fuel in different units.

### 5.5 Diagnostics

- Diagnostic Trouble Codes (DTC) are inconsistently supported; Geotab and Samsara provide fault codes, Webfleet does not expose them in the standard API.  
- Teltonika supports diagnostic data via I/O IDs but requires decoding.

---

## 6. Recommendations for Telemachus v0.2

| Recommendation                                 | Description                                                                                  |
|------------------------------------------------|----------------------------------------------------------------------------------------------|
| Adopt ISO 8601 timestamps                      | Ensure all timestamps use ISO 8601 with timezone for consistency and easy parsing.           |
| Use nested `position` object                    | Group latitude and longitude under `position.lat` and `position.lon` for semantic clarity.  |
| Standardise units                               | Use kilometers for distance, km/h for speed, meters for altitude, and degrees for heading.   |
| Enumerate engine states                         | Define a fixed set of engine status values (`on`, `off`, `unknown`) to unify diverse inputs. |
| Include VIN as optional vehicle identifier     | Support VIN where available but allow missing values for devices without VIN data.           |
| Define diagnostic codes as array of strings    | Use a `diagnostics.dtc` array to list fault codes, supporting multi-code reports.            |
| Support extensible custom fields               | Allow providers to add vendor-specific fields without breaking schema compliance.            |

---

## 7. Pre-Normalised FieldGroups

The following table summarises FieldGroups where Telemachus schema aligns well with existing providers, facilitating rapid adoption:

| FieldGroup              | Alignment Status       | Notes                                           |
|-------------------------|-----------------------|-------------------------------------------------|
| Timestamp               | Fully aligned         | ISO 8601 usage consistent across providers.     |
| Position (lat/lon)      | Fully aligned         | All providers support latitude and longitude.   |
| Speed                   | Mostly aligned        | Units consistent; conversions needed for Teltonika. |
| Heading                 | Mostly aligned        | Degree units standard; naming varies.            |
| Engine State            | Partially aligned     | Value enumerations differ; requires harmonisation. |
| VIN                     | Partially aligned     | Supported except Teltonika; optional in schema.  |
| Odometer                | Partially aligned     | Units differ; standardisation needed.             |
| Fuel Level              | Partially aligned     | Percentage units mostly consistent.               |
| Diagnostics             | Partially aligned     | Varying support and formats; needs unified approach.|

---

## 8. Example Telemachus v0.1 Payload

```json
{
  "time": "2025-10-11T08:34:12Z",
  "position": {
    "lat": 48.852,
    "lon": 2.35,
    "altitude": {
      "m": 35
    }
  },
  "speed": {
    "kmh": 53.2
  },
  "heading": {
    "deg": 210.5
  },
  "engine": {
    "status": "on",
    "fuel": {
      "level_percent": 64.2
    }
  },
  "vehicle": {
    "vin": "VF1ABC..."
  },
  "odometer": {
    "km": 12453.4
  },
  "diagnostics": {
    "dtc": [
      "P0420",
      "P0301"
    ]
  }
}
```

---

## 9. Conclusion

This RFC establishes a foundational comparison of telematics data formats across leading providers and the Telemachus schema. While there is strong convergence on core telemetry data (timestamp, position, speed), divergences remain in domain-specific fields such as engine state, diagnostics, and odometer units. The recommendations herein aim to guide the evolution of Telemachus toward a unified, extensible, and interoperable telematics data model that supports diverse industrial use cases and vendor ecosystems.

Future work includes formalising the v0.2 schema, expanding coverage to advanced diagnostics and driver behaviour data, and defining validation and transformation tools to aid adoption.

---

## 10. Proposed Extended FieldGroups

Below are normalized JSON payload examples for each future FieldGroup, demonstrating consistent structure and field naming for Telemachus v0.2:

### 10.1 Engine FieldGroup
```json
{
  "engine": {
    "status": "on",
    "rpm": 2200,
    "oil_temp_c": 88.5
  }
}
```

### 10.2 Fuel FieldGroup
```json
{
  "engine": {
    "fuel": {
      "level_percent": 67.4,
      "consumption_lph": 5.2,
      "range_km": 410
    }
  }
}
```

### 10.3 Odometer FieldGroup
```json
{
  "odometer": {
    "km": 14523.7,
    "trip_km": 62.4
  }
}
```

### 10.4 Diagnostics FieldGroup
```json
{
  "diagnostics": {
    "dtc": [
      "P0171",
      "P0302"
    ],
    "mil_on": true,
    "last_code_time": "2025-10-11T08:30:00Z"
  }
}
```

### 10.5 Energy FieldGroup (for EV/hybrid support)
```json
{
  "energy": {
    "battery_level_percent": 82,
    "charging_status": "charging",
    "range_km": 320,
    "power_kw": 32.5
  }
}
```

---

## 11. Standardized Units and Field Conventions

The following table lists the field, type, unit, example, and description for each proposed extended field, following the RFC-0001 style:

| Field                         | Type      | Unit     | Example                   | Description                              |
|-------------------------------|-----------|----------|---------------------------|------------------------------------------|
| `engine.status`               | string    | enum     | `"on"`                    | `on`, `off`, `unknown`                   |
| `engine.rpm`                  | integer   | rpm      | `2200`                    | Revolutions per minute                   |
| `engine.oil_temp_c`           | float     | °C       | `88.5`                    | Engine oil temperature                   |
| `engine.fuel.level_percent`   | float     | %        | `67.4`                    | Fuel tank fill level                     |
| `engine.fuel.consumption_lph` | float     | l/h      | `5.2`                     | Liters per hour                          |
| `engine.fuel.range_km`        | float     | km       | `410`                     | Estimated range on current fuel           |
| `odometer.km`                 | float     | km       | `14523.7`                 | Total odometer reading                   |
| `odometer.trip_km`            | float     | km       | `62.4`                    | Trip odometer                            |
| `diagnostics.dtc[]`           | array     | —        | `["P0171"]`               | Diagnostic Trouble Codes                 |
| `diagnostics.mil_on`          | boolean   | —        | `true`                    | Malfunction indicator lamp state         |
| `diagnostics.last_code_time`  | string    | ISO8601  | `"2025-10-11T08:30:00Z"`  | Timestamp of last DTC                    |
| `energy.battery_level_percent`| integer   | %        | `82`                      | EV battery state of charge               |
| `energy.charging_status`      | string    | enum     | `"charging"`              | `charging`, `not_charging`, `full`       |
| `energy.range_km`             | float     | km       | `320`                     | Estimated EV range                       |
| `energy.power_kw`             | float     | kW       | `32.5`                    | Current power delivered/received         |

---

## 12. Extended Mapping Table

This table summarizes how the new extended fields map across Samsara, Webfleet, Geotab, and Teltonika APIs (✓ = direct, ~ = requires transformation, — = not available):

| Field                         | Samsara           | Webfleet          | Geotab            | Teltonika         |
|-------------------------------|-------------------|-------------------|-------------------|-------------------|
| `engine.status`               | `engineState`     | `ignition`        | `ignition`        | AVL ID 239 (~)    |
| `engine.rpm`                  | `engineRpm`       | —                 | `engineRpm`       | AVL ID 10 (~)     |
| `engine.oil_temp_c`           | —                 | —                 | `oilTemperature`  | I/O ID 116 (~)    |
| `engine.fuel.level_percent`   | `fuelPerc`        | `fuelLevel`       | `fuelLevel`       | AVL ID 9 (~)      |
| `engine.fuel.consumption_lph` | —                 | —                 | `fuelRate`        | —                 |
| `engine.fuel.range_km`        | —                 | —                 | `distanceToEmpty` | —                 |
| `odometer.km`                 | `odometerMeters` (~)| `mileage` (~)   | `odometer`        | AVL ID 16 (~)     |
| `odometer.trip_km`            | —                 | —                 | `tripDistance`    | —                 |
| `diagnostics.dtc[]`           | `faultCodes`      | —                 | `faultData`       | I/O ID 70–72 (~)  |
| `diagnostics.mil_on`          | —                 | —                 | `malfunctionIndicator` | —            |
| `diagnostics.last_code_time`  | —                 | —                 | `lastFaultDateTime` | —              |
| `energy.battery_level_percent`| `batteryLevel`    | —                 | `batteryLevel`    | —                 |
| `energy.charging_status`      | `chargingStatus`  | —                 | `chargingStatus`  | —                 |
| `energy.range_km`             | `estimatedRange`  | —                 | `evRange`         | —                 |
| `energy.power_kw`             | `power`           | —                 | `power`           | —                 |

**Notes:**  
* `~` indicates mapping requires unit conversion or calculation.  
* `—` indicates the field is not natively supported or not exposed.

---

## 13. Schema Roadmap

The extended fields outlined above will be integrated into the Telemachus v0.2 schema as optional or nested objects, maintaining backward compatibility with v0.1. Validation rules will be specified for each field (e.g., value ranges, enum values, unit enforcement) and implemented in the Telemachus JSON Schema definition.

**Note:** Extended field groups will be stored in separate files under `schema/extended/`, e.g.:  
- `schema/extended/engine.json`  
- `schema/extended/fuel.json`  
- `schema/extended/odometer.json`  
- `schema/extended/diagnostics.json`  
- `schema/extended/energy.json`

Adapter modules for each provider will be updated to:
- Normalize and map provider-specific fields to the Telemachus schema.
- Perform unit conversions as needed (e.g., meters to kilometers, raw AVL IDs to typed fields).
- Validate incoming data against the updated schema.

Comprehensive documentation and example payloads will be provided for integrators. Future work includes automated conformance testing, versioned schema endpoints, and extensible support for new FieldGroups (e.g., driver behaviour, advanced EV metrics).

---

## 14. References

Below are key API and documentation resources for each provider, with short descriptions for clarity:

| Provider             | Reference URL                                                                                                                     | Description                                                        |
|----------------------|----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| **Webfleet (TomTom)** | [Webfleet.connect API](https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html)                                   | Official API documentation for accessing Webfleet telematics data; covers endpoints, data formats, and integration guidance. |
| **Samsara**          | [Samsara Developer Portal](https://developers.samsara.com/reference/overview)                                                    | Developer documentation for Samsara's RESTful APIs, including telematics, fleet, and sensor data.        |
| **Geotab**           | [MyGeotab SDK](https://developers.geotab.com/myGeotab/introduction/)                                                             | Comprehensive SDK and API documentation for MyGeotab, including JSON-RPC APIs for vehicle data retrieval.|
| **Teltonika**        | [Codec Protocols](https://wiki.teltonika-gps.com/view/Codec)                                                                     | Technical documentation for Teltonika's binary codec protocols (Codec8/Codec8E) used for device communication. |
| **Telemachus**       | [Telemachus Spec v0.1](https://github.com/telemachus3/telemachus-spec)                                                           | GitHub repository for Telemachus open telematics data specification and schema. |
