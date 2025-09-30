# telemachus-py

Python tools for the **Telemachus** open telematics pivot format:
- Export RS3 CSVs → Telemachus dataset (YAML manifest + Parquet tables)
- Validate a dataset.yaml and check referenced tables
- Summarize dataset (rows, columns, time span)


## Quickstart

```bash
tele export \
  --traj tests/data/rs3_trajectory.csv \
  --imu tests/data/rs3_imu.csv \
  --events tests/data/rs3_events.csv \
  --outdir out/tele/$(date -u +%Y%m%dT%H%M%SZ) \
  --freq-hz 10 --vehicle-id VEH-01 --vehicle-type passenger_car

tele validate out/tele/*/dataset.yaml
tele info out/tele/*/dataset.yaml
```

## Schema Conventions

Telemachus defines **two complementary schema layers**:

1. **Manifest schema** (`telemachus/schemas/manifest_schema.py`)  
   - JSON Schema that validates the structure of `dataset.yaml`.  
   - Ensures required keys (`version`, `dataset_id`, `frequency_hz`, `vehicle`, `tables`, …) are present and well-formed.  
   - Describes the container metadata and the list of tables.

2. **Table schemas** (`telemachus/core/schemas.py`)  
   - PyArrow schemas that define the canonical columns and types of each table.  
   - Example: `trajectory` (timestamp, lat, lon, alt, speed), `imu` (acc_x, gyro_x, …), `events` (event_type, severity).  
   - Ensures that each Parquet file matches the expected columns and dtypes.

👉 The **Telemachus specification** is the single source of truth.  
These schemas are implementation mirrors:
- JSON Schema → manifest structure  
- PyArrow Schema → table content

See the [Telemachus Spec](https://telemachus3.github.io/telemachus-spec/01_introduction/) for the formal definition.

## License
AGPL-3
