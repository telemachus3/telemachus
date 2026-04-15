# telemachus-py

Python tools for the **Telemachus** open telematics pivot format:
- Export RS3 CSVs → Telemachus dataset (YAML manifest + Parquet tables)
- Validate a dataset.yaml and check referenced tables
- Summarize dataset (rows, columns, time span)


## Features

- **Export:** Convert RS3 CSV files into a structured Telemachus dataset with manifest and Parquet tables.
- **Validate:** Check the integrity and correctness of dataset manifests and table contents.
- **Summarize:** Generate summaries of datasets including row counts, columns, and time spans.
- **Python API:** Load datasets, read tables as pandas DataFrames, validate data, and compute derived metrics.
- **Integration with RS3:** Seamlessly process RS3 telematics export formats into Telemachus datasets.


## Quickstart

The following example demonstrates exporting RS3 CSV files into a Telemachus dataset, validating the generated manifest, and displaying dataset information. The export command converts trajectory, IMU, and event CSVs into a structured dataset stored in the specified output directory. Validation checks the manifest file for correctness, and info displays summary details about the dataset.

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


## Data Model

The Telemachus dataset organizes telematics data into several main tables, each with canonical columns:

- **trajectory**: Represents vehicle position and motion over time.
  - Typical columns: `timestamp`, `lat`, `lon`, `alt`, `speed`, `heading`
- **imu**: Contains inertial measurement unit data.
  - Typical columns: `timestamp`, `acc_x`, `acc_y`, `acc_z`, `gyro_x`, `gyro_y`, `gyro_z`
- **events**: Logs discrete events occurring during the trip.
  - Typical columns: `timestamp`, `event_type`, `severity`, `description`

These tables are stored as Parquet files referenced by the dataset manifest and are validated against their respective PyArrow schemas.


## Python API

The Python API provides convenient access to Telemachus datasets. You can load a dataset from a manifest file, read individual tables as pandas DataFrames, and validate all tables against their schemas.

Example usage:

```python
from telemachus.core.dataset import Dataset

# Load a dataset from a manifest YAML file
dataset = Dataset.from_manifest("path/to/dataset.yaml")

# Read a table as a pandas DataFrame
df_trajectory = dataset.read_df("trajectory")

# Validate all tables in the dataset
dataset.validate_all()
```

### Working with Frame

The `Frame` class from `telemachus.pandas.frame` extends pandas DataFrames with Telemachus-specific utilities:

```python
from telemachus.pandas.frame import Frame

# Convert a DataFrame to a Frame for additional methods
frame = Frame(df_trajectory)

# Compute time deltas between rows
dt = frame.compute_dt()

# Calculate speed from position data
speed = frame.speed_from_pos()
```

### Validating DataFrames

You can validate pandas DataFrames against the expected PyArrow schema for a table using:

```python
from telemachus.core.validation import validate_df_against_arrow_schema

# Validate a DataFrame against the 'trajectory' schema
validate_df_against_arrow_schema(df_trajectory, "trajectory")
```

### Computing Metrics

The API includes helper functions to compute common telematics metrics:

```python
# Compute time delta between consecutive rows
dt = frame.compute_dt()

# Compute speed from positional data (lat, lon, timestamp)
speed = frame.speed_from_pos()
```

These tools simplify analysis and validation of telematics data within Python.


## Development

To contribute or develop locally, follow these steps:

- Install the package in development mode with dependencies:

```bash
pip install -e .[dev]
```

- Run the test suite using pytest:

```bash
pytest
```

- Lint and format code with ruff and black:

```bash
ruff .
black .
```


## License
GPL-3.0
