# Provider Mappings and Adapter Architecture (v0.2)

This document references RFC-0002 (Comparative APIs) and RFC-0005 (Adapter Architecture) to provide a standardized approach for mapping provider-specific telematics data into the Telemachus schema. These mappings enable interoperability and facilitate adapter-based normalization and integration across diverse telematics providers.

## Introduction

The telematics ecosystem is highly fragmented, with each provider exposing data fields in their own proprietary formats and naming conventions. This fragmentation makes it difficult to integrate, compare, and analyze data across fleets using different providers. **Provider mappings** are essential for achieving interoperability, enabling organizations to unify data from multiple sources into a single schema. By standardizing field names, units, and structures, we can perform meaningful cross-provider analysis, benchmarking, and integration—crucial for both research and business operations.

This section shows how common SaaS telematics providers expose data fields, and how they map into the **Telemachus Core** schema.

---

## Comparative Mapping

| Provider Field       | Example Provider | Telemachus Core Field           | Telemachus Extended FieldGroup (RFC-0004) | Notes |
|----------------------|-----------------|---------------------------------|--------------------------------------------|-------|
| `latitude`, `longitude` | Geotab, Webfleet, Samsara | `position.lat`, `position.lon` | `position.lat`, `position.lon`             | Consistent across providers |
| `speed` (kph)        | Geotab, Webfleet | `motion.speed_kph`              | `motion.speed_kph`                         | Units sometimes in mph → convert |
| `heading` / `bearing`| Samsara          | `position.heading_deg`           | `position.heading_deg`                      | Optional in others |
| `altitude`           | Geotab (limited) | `position.altitude_m`           | `position.altitude_m`                      | Often missing |
| `fuelLevel` (%)      | Geotab           | `powertrain.fuel_pct`           | `energy.fuel_pct`                          | May require OBD-II access |
| `odometer` (km)      | Webfleet         | `powertrain.odometer_km`        | `powertrain.odometer_km`                   | Sometimes reported as miles |
| `engineRpm`          | Samsara          | `powertrain.rpm`                | `powertrain.rpm`                          | Not always accessible |
| `energyConsumed` (kWh) | EV Providers    | (not in Core)                   | `energy.consumed_kwh`                      | From EV APIs |
| `eventType` (e.g. harshBrake) | All 3 | `events[].type`                 | `events[].type`                            | Severity often not provided |
| `satelliteCount`     | Samsara          | `quality.num_satellites`        | `quality.num_satellites`                   | Rarely exposed by SaaS |
| `hdop`               | (none in SaaS)   | `quality.hdop`                  | `quality.hdop`                            | Typically absent |
| `gyroX/Y/Z`          | (none in SaaS)   | `imu.gyro`                      | `imu.gyro`                                | IMU data almost never exposed |
| `accelX/Y/Z`         | (none in SaaS)   | `imu.accel`                     | `imu.accel`                               | Available only in raw device logs |
| `ignitionOn` / `ignitionOff` | Geotab, Webfleet | `events[].type`                | `events[].type`                           | Mapped as events in Telemachus |
| `harshAcceleration`  | All 3           | `events[].type`                 | `events[].type`                           | Severity/threshold varies |
| `VIN`                | Geotab, Samsara  | `source.device_id`              | `source.device_id`                        | Sometimes reported as separate field |
| `driverId`           | Samsara, Webfleet| `context.fleet.driver_id`       | `context.fleet.driver_id`                  | Sometimes unavailable or optional |

---

### Alignment with RFCs

- **RFC-0002 (Comparative API definitions):** This mapping aligns provider-specific fields to a common schema, enabling cross-provider data interoperability and comparative analytics.
- **RFC-0004 (Extended FieldGroups):** The new extended field groups provide richer semantic grouping of related data (e.g., `energy`, `powertrain`), supporting advanced use cases such as EV data integration.
- **RFC-0005 (Adapter Architecture):** These mappings underpin the adapter layer, which performs normalization, metadata enrichment, and schema version tagging to ensure consistent and extensible data ingestion.

---

### Key Insights

- **Consistency issues**: Field names and units vary widely across providers, requiring normalization.
- **Unit conversions**: Speed and distance may be reported in either metric or imperial units and must be converted for consistency.
- **Missing quality/IMU data**: GNSS quality (e.g., satellite count, HDOP) and IMU sensor data are rarely available via SaaS APIs.
- **Optional vs required fields**: Some fields are always present (e.g., GPS), while others (powertrain, driver, quality) are optional or provider-specific.
- **Adapter normalization**: The adapter architecture (RFC-0005) enables automated data normalization, metadata enrichment, and tagging with schema versions (`schema_version` field) to maintain data provenance and compatibility.
- **Metadata enrichment**: Adapters can add contextual metadata, improving downstream analytics and integration.
- **Schema version tagging**: Use of `schema_version` ensures datasets are clearly versioned, facilitating evolution and backward compatibility.

## Observations

- **Strong overlap**: GPS position, speed, and events exist across all providers.  
- **Partial overlap**: Powertrain data (fuel, odometer, RPM) vary by provider and often need OBD-II integration.  
- **Gaps**: IMU and GNSS quality fields are almost never available via SaaS APIs.  
- **Implication**: Telemachus Core acts as a superset. Providers can fill what they have, and leave the rest empty.
- **Device-level detail**: Teltonika (device-level integration) exposes more raw fields—including IMU and GNSS quality—compared to typical SaaS APIs, which are more limited in scope.

---

## Conclusion

By mapping provider-specific fields into **Telemachus Core**, we achieve **cross-provider interoperability**.  
Even if some providers expose only GPS + events, while others add powertrain data, the unified format makes datasets **comparable** and prepares the ground for **Telemachus Completeness Score (TCS)**.  
This mapping supports both research—by enabling fair comparisons across providers—and business, by simplifying multi-fleet and multi-provider integration into a single analytics pipeline.  
Furthermore, as described in RFC-0009 (RS3 Integration Pipeline), these provider mappings enable hybrid datasets combining real and simulated data to enhance analytics and testing workflows.