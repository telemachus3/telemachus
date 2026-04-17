# PVS — Telemachus Format (Local Reproduction Only)

The PVS dataset (Menegazzo & von Wangenheim, 2020) is licensed under **CC-BY-NC-ND-4.0**,
which prohibits redistribution of derivative works. This directory contains the conversion
tooling and manifest, but **not the data itself**.

## Prerequisites

- Python 3.10+
- `telemachus` installed (`pip install telemachus`)
- A Kaggle account (free)

## Step 1 — Download from Kaggle

```bash
# Option A: via Kaggle CLI
pip install kaggle
kaggle datasets download -d jefmenegazzo/pvs-passive-vehicular-sensors-datasets
unzip pvs-passive-vehicular-sensors-datasets.zip -d /path/to/pvs/

# Option B: manual download
# Go to https://www.kaggle.com/datasets/jefmenegazzo/pvs-passive-vehicular-sensors-datasets
# Download and extract to /path/to/pvs/
```

Expected structure after extraction:

```
/path/to/pvs/
├── PVS 1/
│   ├── dataset_gps_mpu_left.csv    (81 MB)
│   ├── dataset_gps_mpu_right.csv   (81 MB)
│   ├── dataset_gps.csv             (211 KB)
│   ├── dataset_labels.csv          (4 MB)
│   ├── dataset_settings_left.csv
│   └── dataset_settings_right.csv
├── PVS 2/
│   └── ...
└── PVS 9/
    └── ...
```

## Step 2 — Convert to Telemachus format

```bash
tele convert pvs /path/to/pvs/ -o datasets/pvs/ --placement dashboard --side left
```

Or programmatically:

```python
from telemachus.adapters.pvs import load

df = load("/path/to/pvs/", placement="dashboard", side="left")
df.to_parquet("datasets/pvs/pvs-telemachus-dashboard-left.parquet", index=False)
```

### Available placements

| Placement | Description | Recommended for |
|-----------|-------------|-----------------|
| `dashboard` | Mounted on dashboard | Closest to commercial telematics box |
| `above_suspension` | Above suspension mount | Vehicle dynamics research |
| `below_suspension` | Below suspension mount | Road quality analysis |

### Available sides

Each vehicle has two MPU-9250 sensors: `left` and `right`.

## Step 3 — Verify

```bash
tele validate datasets/pvs/ --level basic
```

Expected output:

```
pvs-telemachus-dashboard-left.parquet: 1,080,905 rows, 9 trips — PASS (basic)
```

Checksum verification:

```bash
shasum -a 256 -c SHA256SUMS
```

## Step 4 — Use in papers

```python
import telemachus as tele

df = tele.read("datasets/pvs/pvs-telemachus-dashboard-left.parquet")
report = tele.validate(df, profile="full", level="basic")
```

## Dataset characteristics

| Property | Value |
|----------|-------|
| Hardware | MPU-9250 (InvenSense) |
| Accel rate | 100 Hz |
| Gyro rate | 100 Hz (ground truth) |
| Magneto rate | 100 Hz |
| GPS rate | ~1 Hz |
| Trips | 9 (3 vehicles x 3 drivers) |
| Rows | 1,080,905 |
| Location | Curitiba, Parana, Brazil |
| Period | December 2019 |
| License | CC-BY-NC-ND-4.0 |

## Citation

```
Menegazzo, J. & von Wangenheim, A. (2020).
PVS — Passive Vehicular Sensors datasets. Kaggle.
https://www.kaggle.com/datasets/jefmenegazzo/pvs-passive-vehicular-sensors-datasets
```

Format specification:

```
Edet, S. (2026). Telemachus Specification v0.8.
DOI: 10.5281/zenodo.19609019
```
