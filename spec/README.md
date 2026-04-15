[![Docs](https://img.shields.io/badge/docs-online-blue)](https://telemachus3.github.io/telemachus-spec/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)
# Telemachus Specification (v0.8 — Draft)

**Telemachus** is an open RFC-driven pivot standard for high-frequency mobility and telematics data.
It bridges simulated data (RoadSimulator3) and real-world fleet sources (Webfleet, Samsara, Geotab, Teltonika) under a unified, open schema.

## Vision
- 📡 Integrate GNSS, IMU, motion, and powertrain signals.
- 🧱 Layered data model: D0 (raw device) → D1 (cleaned + contextualized) → D2 (events).
- 🧭 Support simulated (RoadSimulator3) and industrial fleet data sources.
- 🌍 Enable contextual enrichment (weather, road type, safety, emissions).
- ⚖️ Open, MIT-licensed format — reference adapters and validators released alongside.
- 🔬 Evolve through RFCs and open governance (RFC-0011).

## Current state

| Artifact | Version |
|----------|---------|
| Latest released spec | **v0.2** (2025-10-13) — stable core schema |
| Latest draft | **v0.8** — D0 device layer (RFC-0013) + Dataset Manifest (RFC-0014) |

The v0.8 draft introduces the **Telemachus Device Format** (raw device output contract, AccPeriod frame tracking, CarrierState classification) and the normative **Dataset Manifest** sidecar (RFC-0014) — see `rfcs/` for both.

## Quickstart
```bash
# Validate payload data against the v0.2 core schema
ajv validate -s schemas/telemachus_core_v0.2.json -d examples/*.jsonl

# Validate a dataset manifest against the v0.8 manifest schema (RFC-0014)
ajv validate -s schemas/telemachus_manifest_v0.8.json -d path/to/manifest.yaml
```

## Repositories
- [telemachus-py](https://github.com/telemachus3/telemachus-py) – Python SDK & validator
- [telemachus-cli](https://github.com/telemachus3/telemachus-cli) – CLI tools for datasets and conversions
- [telemachus-datasets](https://github.com/telemachus3/telemachus-datasets) – Public example datasets

## Citation
S. Edet (2025). *Telemachus Specification (v0.2)*.
Zenodo. https://doi.org/10.5281/zenodo.17228092

## Roadmap & Changelog
- [Roadmap](docs/10_roadmap.md)
- [Changelog](CHANGELOG.md)

## RFCs
- [RFC Index](https://github.com/telemachus3/telemachus-spec/tree/main/rfcs)
- RFC-0001 – Core Schema (v0.2)
- RFC-0003 – Dataset Specification
- RFC-0004 – Extended FieldGroups
- RFC-0005 – Adapter Architecture
- RFC-0007 – Validation Framework
- RFC-0009 – RoadSimulator3 Integration Pipeline
- RFC-0011 – Versioning & Governance
- RFC-0013 – Telemachus Device Format (v0.7)
- RFC-0014 – Dataset Manifest (v0.8, Draft)

## CLI Examples
```bash
# Validate a file
telemachus validate examples/geotab.json

# Convert JSON/JSONL directory to Parquet
telemachus to-parquet examples/ -o fleet.parquet

# Compute Completeness Score
telemachus tcs fleet.parquet
```

## License
MIT