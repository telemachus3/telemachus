[![PyPI](https://img.shields.io/pypi/v/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Python](https://img.shields.io/pypi/pyversions/telemachus.svg)](https://pypi.org/project/telemachus/)
[![Docs](https://img.shields.io/badge/docs-telemachus3.org-blue)](https://telemachus3.org)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19609019.svg)](https://doi.org/10.5281/zenodo.19609019)
[![License](https://img.shields.io/badge/license-MIT%20%2F%20AGPL--3.0-green)](LICENSE)

# Telemachus

**Telemachus** is an open, Parquet-native pivot format for high-frequency
mobility and telematics data. It bridges the rigor of scientific
kinematics (multi-rate GNSS+IMU at 10-100 Hz, accelerometer gravity
frame tracking) and scalable fleet analytics (OBD, trip metadata,
carrier state) in a single format — instantly queryable in Pandas,
Spark, DuckDB, or Athena.

**Why not an existing standard?** Robotics formats (ROS bags) handle
the physics but aren't columnar. Fleet APIs (Geotab, Samsara) handle
scale but abstract away raw sensors. IoT protocols (MQTT, SensorThings)
handle transport but not analytical storage. Telemachus fills the gap:
raw sensor data, SI units, flat columns, Parquet files, Python SDK.

This repository is the **monorepo** consolidating spec, Python SDK,
CLI, and reference datasets into a single source of truth.

## Layout

| Directory | What |
|-----------|------|
| [`spec/`](spec/) | SPECs + JSON Schemas — the normative specification |
| [`python-sdk/`](python-sdk/) | Python SDK & validator (`telemachus` package on PyPI) |
| [`python-cli/`](python-cli/) | CLI tools (`tele` command, bundled with the SDK) |
| [`datasets/`](datasets/) | Open datasets in Telemachus format — AEGIS, STRIDE, RS3, PVS |
| [`docs/`](docs/) | Site sources (mkdocs) + the AEGIS demo notebook |

## Versions

| Artifact | Version |
|----------|---------|
| **Current spec** | **v0.8** (2026-04-16) — consolidated into 4 SPEC pillars |

The v0.8 specification defines the Telemachus record format (column
contracts, AccPeriod frame tracking, CarrierState classification, burst
sampling, magnetometer support) and the normative **Dataset Manifest**.

## Quickstart

### Install
```bash
pip install telemachus
```

### Try it in 5 minutes

The [AEGIS demo notebook](docs/notebooks/aegis-demo.ipynb)
([open in Colab](https://colab.research.google.com/github/telemachus3/telemachus/blob/main/docs/notebooks/aegis-demo.ipynb))
downloads a real Open dataset from Zenodo, loads it, and plots one trip.

### Read a dataset
```python
import telemachus as tele

df = tele.read("path/to/manifest.yaml")   # or directly a .parquet
print(tele.sensor_profile(df))            # → "gps+imu+gyro"
```

### Validate
```bash
tele validate path/to/dataset/ --level full     # full dataset (parquet + manifest)
tele validate path/to/data.parquet --level basic
tele info path/to/manifest.yaml                 # dataset summary
```

### Convert an Open dataset
```bash
tele convert aegis  /path/to/aegis/csvs      -o datasets/aegis/
tele convert pvs    /path/to/pvs/trips       -o datasets/pvs/    --placement dashboard
tele convert stride /path/to/stride/road_data -o datasets/stride/ --category driving
```

## Specifications (v0.8)

The spec was consolidated in April 2026 from 10 RFCs into 4 pillars:

| SPEC | Title | Scope |
|------|-------|-------|
| [SPEC-01](spec/SPEC-01-record-format.md) | Telemachus Record Format | Column definitions, functional groups (GNSS, IMU, Vehicle I/O), validation rules, hardware mapping |
| [SPEC-02](spec/SPEC-02-manifest.md) | Dataset Manifest | manifest.yaml schema, sensors, AccPeriods, CarrierState, inheritance rules |
| [SPEC-03](spec/SPEC-03-adapters-validation.md) | Adapters & Validation | Adapter interface, Open dataset specs (AEGIS/PVS/STRIDE), validation framework, CLI |
| [SPEC-04](spec/SPEC-04-governance.md) | Governance & Versioning | Versioning model, release checklist, IP channel separation |

Previous RFCs (0001→0014) are archived in [`spec/rfcs/`](spec/rfcs/) with deprecation notices pointing to the corresponding SPEC.

## Citation

```
S. Edet (2026). Telemachus Specification v0.8 — Open Parquet-Native
Format for High-Frequency Telematics Data. Zenodo.
https://doi.org/10.5281/zenodo.19609019
```

Open datasets shipped in Telemachus format:

- **AEGIS** (Austria, GNSS+IMU+Gyro+OBD, CC-BY-4.0) — [10.5281/zenodo.19609044](https://doi.org/10.5281/zenodo.19609044)
- **STRIDE** (Bangladesh, smartphone 100 Hz, CC-BY-4.0) — [10.5281/zenodo.19609053](https://doi.org/10.5281/zenodo.19609053)
- **RS3** (Le Havre synthetic, CC0-1.0) — [10.5281/zenodo.19609057](https://doi.org/10.5281/zenodo.19609057)

## License

Specification, schemas, datasets: MIT / CC-BY / CC0 (per-file).
Python SDK: AGPL-3.0-only. See [`LICENSE`](LICENSE).
