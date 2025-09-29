


# Provider Mappings

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

---

## Observations

- **Strong overlap**: GPS position, speed, and events exist across all providers.  
- **Partial overlap**: Engine data (fuel, odometer, RPM) vary by provider and often need OBD-II integration.  
- **Gaps**: IMU and GNSS quality fields are almost never available via SaaS APIs.  
- **Implication**: Telemachus Core acts as a superset. Providers can fill what they have, and leave the rest empty.

---

## Conclusion

By mapping provider-specific fields into **Telemachus Core**, we achieve **cross-provider interoperability**.  
Even if some providers expose only GPS + events, while others add engine data, the unified format makes datasets **comparable** and prepares the ground for **Telemachus Completeness Score (TCS)**.