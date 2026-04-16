[![Docs](https://img.shields.io/badge/docs-online-blue)](https://telemachus3.github.io/telemachus/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

# Telemachus

**Telemachus** is an open RFC-driven pivot standard for high-frequency
mobility and telematics data. It bridges simulated data
(RoadSimulator3) and real-world fleet sources (Webfleet, Samsara,
Geotab, Teltonika) under a unified, open schema.

This repository is the **monorepo** that consolidates the four previous
`telemachus-*` repositories (spec, Python SDK, CLI, datasets) into a
single source of truth.

## Layout

| Directory | What |
|-----------|------|
| [`spec/`](spec/) | SPECs + JSON Schemas — the normative specification |
| [`python-sdk/`](python-sdk/) | Python SDK & validator (`telemachus` package) |
| [`python-cli/`](python-cli/) | CLI tools (`telemachus-cli`, validate / convert / score) |
| [`datasets/`](datasets/) | Reference datasets & manifests (samples + pointers) |

## Versions

| Artifact | Version |
|----------|---------|
| **Current spec** | **v0.8** (2026-04-16) — consolidated into 4 SPEC pillars |

The v0.8 specification introduces the layered Telemachus processing layers data model,
AccPeriod frame tracking, CarrierState classification, burst sampling,
magnetometer support, and the normative **Dataset Manifest** sidecar.

## Quickstart

### Install
```bash
pip install -e python-sdk
```

### Read a dataset
```python
import telemachus as tele

# Load from a manifest (returns a pandas DataFrame)
df = tele.read("path/to/manifest.yaml")
print(tele.sensor_profile(df))  # → "gps+imu+gyro"
```

### Validate
```bash
# Validate a dataset (Telemachus parquet + manifest)
tele validate path/to/dataset/ --level full

# Quick D0 check on a parquet file
tele validate path/to/d0.parquet --level d0

# Dataset info
tele info path/to/manifest.yaml
```

### Convert an Open dataset to D0
```bash
# Download AEGIS from Zenodo, then convert to Telemachus format
tele convert aegis /path/to/aegis/csvs --outdir datasets/aegis/
tele convert pvs /path/to/pvs/trips --outdir datasets/pvs/
tele convert stride /path/to/stride/road_data --outdir datasets/stride/
```

### Validate a manifest schema (JSON Schema)
```bash
ajv validate -s spec/schemas/telemachus_manifest_v0.8.json -d path/to/manifest.yaml
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

## History

This monorepo preserves the full Git history of the four source
repositories. Each subdirectory contains the historical commits of
its respective former repo (rewritten via `git filter-repo
--to-subdirectory-filter`).

Former repos (now archived):
- `telemachus-spec` → [`spec/`](spec/)
- `telemachus-py` → [`python-sdk/`](python-sdk/)
- `telemachus-cli` → [`python-cli/`](python-cli/)
- `telemachus-datasets` → [`datasets/`](datasets/)

## Citation

```
S. Edet (2025). Telemachus Specification.
Zenodo. https://doi.org/10.5281/zenodo.17228092
```

## License

MIT — see [`LICENSE`](LICENSE).
