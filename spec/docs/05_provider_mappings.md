



# Provider Mappings

## Introduction

The telematics ecosystem is highly fragmented, with each provider exposing data fields in their own proprietary formats and naming conventions. This fragmentation makes it difficult to integrate, compare, and analyze data across fleets using different providers. **Provider mappings** are essential for achieving interoperability, enabling organizations to unify data from multiple sources into a single schema. By standardizing field names, units, and structures, we can perform meaningful cross-provider analysis, benchmarking, and integration—crucial for both research and business operations.

This section shows how common SaaS telematics providers expose data fields, and how they map into the **Telemachus Core** schema.

---

## Comparative Mapping

| Provider Field       | Example Provider | Telemachus Core Field           | Notes |
|----------------------|-----------------|---------------------------------|-------|
| `latitude`, `longitude` | Geotab, Webfleet, Samsara | `position.lat`, `position.lon` | Consistent across providers |
| `speed` (kph)        | Geotab, Webfleet | `motion.speed_kph`              | Units sometimes in mph → convert |
| `heading` / `bearing`| Samsara          | `position.heading_deg`           | Optional in others |
| `altitude`           | Geotab (limited) | `position.altitude_m`           | Often missing |
| `fuelLevel` (%)      | Geotab           | `engine.fuel_pct`               | May require OBD-II access |
| `odometer` (km)      | Webfleet         | `engine.odometer_km`            | Sometimes reported as miles |
| `engineRpm`          | Samsara          | `engine.rpm`                    | Not always accessible |
| `eventType` (e.g. harshBrake) | All 3 | `events[].type`                 | Severity often not provided |
| `satelliteCount`     | Samsara          | `quality.num_satellites`        | Rarely exposed by SaaS |
| `hdop`               | (none in SaaS)   | `quality.hdop`                  | Typically absent |
| `gyroX/Y/Z`          | (none in SaaS)   | `imu.gyro`                      | IMU data almost never exposed |
| `accelX/Y/Z`         | (none in SaaS)   | `imu.accel`                     | Available only in raw device logs |
| `ignitionOn` / `ignitionOff` | Geotab, Webfleet | `events[].type`                | Mapped as events in Telemachus |
| `harshAcceleration`  | All 3           | `events[].type`                 | Severity/threshold varies |
| `VIN`                | Geotab, Samsara  | `source.device_id`              | Sometimes reported as separate field |
| `driverId`           | Samsara, Webfleet| `context.fleet.driver_id`       | Sometimes unavailable or optional |

---

### Key Insights

- **Consistency issues**: Field names and units vary widely across providers, requiring normalization.
- **Unit conversions**: Speed and distance may be reported in either metric or imperial units and must be converted for consistency.
- **Missing quality/IMU data**: GNSS quality (e.g., satellite count, HDOP) and IMU sensor data are rarely available via SaaS APIs.
- **Optional vs required fields**: Some fields are always present (e.g., GPS), while others (engine, driver, quality) are optional or provider-specific.

## Observations

- **Strong overlap**: GPS position, speed, and events exist across all providers.  
- **Partial overlap**: Engine data (fuel, odometer, RPM) vary by provider and often need OBD-II integration.  
- **Gaps**: IMU and GNSS quality fields are almost never available via SaaS APIs.  
- **Implication**: Telemachus Core acts as a superset. Providers can fill what they have, and leave the rest empty.
- **Device-level detail**: Teltonika (device-level integration) exposes more raw fields—including IMU and GNSS quality—compared to typical SaaS APIs, which are more limited in scope.

---

## Conclusion

By mapping provider-specific fields into **Telemachus Core**, we achieve **cross-provider interoperability**.  
Even if some providers expose only GPS + events, while others add engine data, the unified format makes datasets **comparable** and prepares the ground for **Telemachus Completeness Score (TCS)**.
This mapping supports both research—by enabling fair comparisons across providers—and business, by simplifying multi-fleet and multi-provider integration into a single analytics pipeline.