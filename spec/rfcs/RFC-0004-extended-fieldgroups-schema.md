---
RFC: 0004
Title: Extended FieldGroups Schema
Version: 0.1-draft  
Status: Deprecated
Deprecated: 2026-04-16
Superseded_by: ../SPEC-01-record-format.md
Author: Sébastien Edet  
Date: 2025-10-13  
Project: Telemachus Specification  
---

> **DEPRECATED** — Extended FieldGroups (engine, fuel, odometer, diagnostics, energy) are now covered by [SPEC-01 §2.5 Vehicle I/O](../SPEC-01-record-format.md) for D0-level fields, and remain D1+ concerns for enriched fields. Kept for historical reference.

## 1. Purpose

This RFC defines the **Extended FieldGroups Schema** for Telemachus Specification v0.2.  
It builds upon the core model defined in RFC-0001 and the industrial mapping introduced in RFC-0002.  
The goal is to standardize additional telemetry domains commonly found in fleet APIs (e.g. Webfleet, Samsara, Geotab) and in RS3 simulation outputs.

---

## 2. Scope

This document describes the structure and semantics of five extended FieldGroups:
- `engine` — engine and ignition data  
- `fuel` — consumption and tank-related data  
- `odometer` — distance and mileage information  
- `diagnostics` — vehicle health and OBD metrics  
- `energy` — EV-specific energy and battery data  

Each FieldGroup is defined as a JSON Schema extension compatible with the Telemachus Core model (RFC-0001).

---

## 3. Relationship to Core Schema

The Extended FieldGroups complement, but do not replace, the Core Fields defined in RFC-0001 (`time`, `position`, `speed`, `heading`, `acceleration`).  
A valid Telemachus Record may include one or several Extended FieldGroups.  
Compatibility rules:
- All FieldGroups share the same timestamp and alignment model.  
- Extended schemas live under `schema/extended/`.  
- Each FieldGroup schema inherits from `core/record.schema.json`.

---

## 4. File Organization

```
schema/
 ├── core/
 │    └── record.schema.json
 └── extended/
      ├── engine.schema.json
      ├── fuel.schema.json
      ├── odometer.schema.json
      ├── diagnostics.schema.json
      └── energy.schema.json
```

---

## 5. FieldGroup: Engine

| Field                | Type   | Unit            | Example | Description               |
|----------------------|--------|-----------------|---------|---------------------------|
| `engine.status`       | string | enum(`on`,`off`,`idle`) | `on`    | Engine operational state  |
| `engine.rpm`          | number | `rev/min`       | 2300    | Engine speed              |
| `engine.coolant_temp_c` | number | `°C`           | 92.1    | Coolant temperature       |
| `engine.load_pct`     | number | `%`             | 45.2    | Current engine load percentage |
| `engine.oil_temp_c`   | number | `°C`             | 88.5    | Oil temperature           |

---

## 6. FieldGroup: Fuel

| Field              | Type   | Unit            | Example | Description          |
|--------------------|--------|-----------------|---------|----------------------|
| `fuel.level_pct`   | number | `%`             | 63.5    | Remaining fuel level  |
| `fuel.rate_lph`    | number | `L/h`           | 4.2     | Instantaneous fuel rate |
| `fuel.used_l`      | number | `L`             | 28.6    | Cumulative fuel used  |
| `fuel.range_km`    | number | `km`            | 145.0   | Estimated remaining range |
| `fuel.type`        | string | enum(`diesel`,`petrol`,`gas`) | `diesel` | Fuel type          |

---

## 7. FieldGroup: Odometer

| Field              | Type   | Unit            | Example | Description          |
|--------------------|--------|-----------------|---------|----------------------|
| `odometer.total_km` | number | `km`            | 58412.2 | Total accumulated distance |
| `odometer.trip_km`  | number | `km`            | 12.8    | Trip distance since reset |
| `odometer.source`   | string | enum(`can`,`gps`,`simulated`) | `can` | Source of odometer data |

---

## 8. FieldGroup: Diagnostics

| Field                  | Type    | Unit | Example | Description                        |
|------------------------|---------|------|---------|----------------------------------|
| `diagnostics.dtc_count` | integer | -    | 2       | Number of active Diagnostic Trouble Codes |
| `diagnostics.mil_status` | boolean | -    | true    | Malfunction Indicator Light (MIL) active |
| `diagnostics.obd_voltage_v` | number | `V`  | 13.8    | System voltage                   |
| `diagnostics.throttle_pct` | number | `%`  | 22.0    | Throttle position percentage     |

---

## 9. FieldGroup: Energy (EV)

| Field                    | Type   | Unit            | Example | Description           |
|--------------------------|--------|-----------------|---------|-----------------------|
| `energy.battery_level_pct` | number | `%`             | 82.0    | Battery state of charge |
| `energy.battery_voltage_v` | number | `V`             | 370.2   | Battery voltage        |
| `energy.battery_temp_c`   | number | `°C`             | 33.5    | Battery temperature    |
| `energy.energy_used_kwh`  | number | `kWh`            | 12.8    | Total energy consumed  |
| `energy.charging_status`  | string | enum(`charging`,`discharging`,`idle`) | `charging` | Charging state |

---

## 10. Schema Conventions

All Extended FieldGroups follow the conventions from RFC-0001:
- Flat dot-notation field names (`group.field`).
- SI units unless otherwise stated.
- Optional fields are nullable unless marked as `required`.
- Field naming follows `snake_case` for suffixes (`_pct`, `_c`, `_v`).

Each schema is self-descriptive and versioned using the `$id` and `$schema` properties.

---

## 11. Example Combined Record

```json
{
  "time": "2025-10-13T10:15:00.000Z",
  "position.lat": 48.8566,
  "position.lon": 2.3522,
  "speed.kmh": 78.4,
  "heading.deg": 192.1,
  "engine.rpm": 2400,
  "fuel.level_pct": 64.3,
  "odometer.total_km": 58412.2,
  "diagnostics.dtc_count": 0,
  "energy.battery_level_pct": null
}
```

---

## 12. Validation and Integration

Validation is handled through the Telemachus schema registry:
```
schema/extended/<fieldgroup>.schema.json
```

Each file:
- defines `type`, `unit`, and `description` properties for each field,  
- includes a `$ref` to `core/record.schema.json`,  
- may include `required` or `enum` constraints.

The `telemachus validate` command detects and validates extended schemas automatically when `--extended` is provided.

---

## 13. Future Extensions

Planned additions:
- `safety` FieldGroup (airbags, ABS, traction control)
- `climate` FieldGroup (HVAC status, cabin temperature)
- `gps` FieldGroup (GNSS accuracy, satellite count)
- `energy.dc_fast_charge_kw` (DC charging power field)

These will be defined in future RFCs as part of Telemachus v0.3.

---

## 14. References

- RFC-0001 — *Telemachus Core 0.2*  
- RFC-0002 — *Comparative Telematics API Formats*  
- RFC-0003 — *Dataset Specification 0.2*  
- RFC-0007 — *Validation Framework and CLI Rules*  
- Webfleet Connect API — https://www.webfleet.com/static/help/webfleet-connect/en_gb/index.html  
- Samsara API — https://developers.samsara.com/reference/overview  
- Geotab API — https://developers.geotab.com/myGeotab/introduction/  
- Teltonika Codec — https://wiki.teltonika-gps.com/view/Codec  
- Telemachus Specification — https://telemachus3.github.io/telemachus-spec  

---

## 15. Conclusion

This RFC formalizes the structure and naming conventions for Extended FieldGroups in Telemachus.  
It ensures compatibility with both industrial fleet telematics APIs and simulated RS3 datasets, enabling a unified representation of extended vehicle signals across energy, engine, and diagnostic domains.
