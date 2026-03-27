# Open Datasets — D0 Compatibility Reference

Datasets evaluated against the Telemachus format schema (RFC-0013) for adapter development and pipeline validation.

## Validated Sources

### UAH-DriveSet (Universidad de Alcala)

| Field | Value |
|-------|-------|
| Country | **Spain (Madrid region)** |
| Carto required | OSRM extract: spain-latest.osm.pbf, SRTM tiles: N40 |
| GPS | lat, lon, altitude, speed (m/s), course, h_accuracy — **1 Hz** |
| IMU | accel 3-axis in **G-force** (x 9.80665 for m/s2) — **10 Hz** |
| Gyroscope | **NO** (roll/pitch/yaw are orientation, not angular rate) |
| Labels | Driver behavior (normal / drowsy / aggressive), road type (motorway / secondary) |
| Trips | 6 drivers x 3 behaviors x 2 road types ~ 36 trips, 500+ min |
| Format | Space-delimited .txt (RAW_ACCELEROMETERS.txt, RAW_GPS.txt) |
| Download | ~3-5 GB (includes video) |
| License | Academic (IEEE ITSC 2016) |
| Link | http://www.robesafe.uah.es/personal/eduardo.romera/uah-driveset/ |
| Adapter | `telemachus adapt --source uah-driveset` |
| RFC gaps found | No absolute timestamp, accel in G not m/s2, orientation != gyro |

### PVS — Passive Vehicular Sensors (Kaggle)

| Field | Value |
|-------|-------|
| Country | **Brazil (Curitiba region)** |
| Carto required | OSRM extract: south-america/brazil-latest.osm.pbf |
| GPS | lat, lon, altitude, speed (m/s), accuracy — **1 Hz** |
| IMU | accel 3-axis (m/s2) + **gyro 3-axis (deg/s)** — **100 Hz** |
| Labels | Road surface (dirt/cobblestone/asphalt), condition, speed bumps |
| Trips | 9 recordings, 10-14 km each, 3 vehicles, 3 drivers |
| Format | CSV |
| Download | 44.5 GB (includes video; sensor-only much smaller) |
| License | **CC BY-NC-ND 4.0** (non-commercial, no derivatives) |
| Link | kaggle.com/datasets/jefmenegazzo/pvs-passive-vehicular-sensors-datasets |
| Adapter | Not yet implemented |
| Notes | True gyro data available. License restrictive. Downsample 100Hz -> 10Hz needed. |

### comma2k19 (comma.ai)

| Field | Value |
|-------|-------|
| Country | **USA (California, highway CA-280)** |
| Carto required | OSRM extract: us-west-latest.osm.pbf |
| GPS | lat, lon, speed, altitude, bearing — **~1 Hz** |
| IMU | accel + gyro (calibrated) — **100 Hz** |
| Labels | None (CAN bus data available for deriving events) |
| Format | capnp binary (requires openpilot tools to decode) |
| Download | ~100 GB |
| License | MIT |
| Link | github.com/commaai/comma2k19 |
| Adapter | Not implemented — impractical (binary format, huge size) |
| Notes | Highway-only driving. Rich CAN data but complex extraction. |

### Smartphone IMU Road Accident Detection (Kaggle)

| Field | Value |
|-------|-------|
| Country | **Unknown** |
| Carto required | None (too few rows for map matching) |
| GPS | lat, lon — embedded in CSV |
| IMU | accel 3-axis + **gyro 3-axis** |
| Labels | **Crash_Label (0=normal, 1=accident)** |
| Format | CSV (single file) |
| Download | **742 KB** |
| License | CC0 Public Domain |
| Link | kaggle.com/datasets/drabdulbari/smartphone-imu-road-accident-detection-dataset |
| Adapter | Not yet implemented |
| Notes | Only 8K rows. Has gyroscope — useful for IMU calibration validation. |

### AEGIS Automotive Sensor Data (Zenodo)

| Field | Value |
|-------|-------|
| Country | **Austria (Graz)** |
| Carto required | OSRM extract: europe/austria-latest.osm.pbf |
| GPS | Yes (GPS sensor) |
| IMU | accel 3-axis + **gyro 3-axis** + OBD2/CAN |
| Labels | None |
| Format | CSV in ZIP |
| Download | **37 MB** |
| License | CC BY 4.0 |
| Link | zenodo.org/records/820576 |
| Adapter | Not yet implemented |
| Notes | 35 trips, 1 driver, 1 vehicle. Small and clean. |

### Harnessing Smartphone Sensors (Figshare / Nature Scientific Data)

| Field | Value |
|-------|-------|
| Country | **Bangladesh (Rajshahi)** |
| Carto required | OSRM extract: asia/bangladesh-latest.osm.pbf |
| GPS | lat, lon, alt, speed, bearing, accuracy (Location.csv) |
| IMU | accel 3-axis + **gyro 3-axis** + magnetometer + gravity |
| Labels | **Road anomalies (bumps, potholes) + behavior (aggressive/standard/slow)** |
| Format | CSV (separate files per sensor) |
| Download | Moderate (~100 MB estimated) |
| License | CC BY 4.0 |
| Link | doi.org/10.6084/m9.figshare.25460755 |
| Paper | nature.com/articles/s41597-024-04193-0 |
| Adapter | Not yet implemented |
| Notes | 10 sensor types, published in Nature Scientific Data. Richest labeled dataset. |

## Sources Not Usable for D0

| Dataset | Country | Issue |
|---------|---------|-------|
| jair-jr Driver Behavior | Brazil | No GPS — IMU only |
| Driving Behavior (Kaggle/outofskills) | ? | No GPS, 2 Hz only |
| Mendeley Driver Behavior | ? | No GPS |

## Real-World Sources (Real-World Commercial Sources (anonymized))

| Device | Country | GPS | IMU | Gyro | Protocol |
|--------|---------|-----|-----|------|----------|
| Teltonika (via Flespi) | **France** | Yes (1 Hz) | Accel 3-axis | **No** | MQTT -> Flespi (modified by commercial integrator to expose IMU) |

## Carto Stack Requirements by Country

| Country | OSRM extract | SRTM tiles | DEM alternative |
|---------|-------------|------------|-----------------|
| France (Normandie) | france/normandie-latest.osm.pbf | N48-N50 | IGN RGeAlti |
| Spain (Madrid) | spain-latest.osm.pbf | N40 | SRTM only |
| Brazil (Curitiba) | south-america/brazil-south-latest.osm.pbf | S25-S26 | SRTM only |
| USA (California) | us-west-latest.osm.pbf | N37 | SRTM only |
