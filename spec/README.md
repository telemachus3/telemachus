[![Docs](https://img.shields.io/badge/docs-online-blue)](https://telemachus3.github.io/telemachus-spec/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17228092.svg)](https://doi.org/10.5281/zenodo.17228092)
# Telemachus Specification (v0.2)

**Telemachus** is an open RFC-driven pivot standard for high-frequency mobility and telematics data.  
It bridges simulated data (RS3) and real-world fleet sources (Webfleet, Samsara, Geotab, Teltonika) under a unified, open schema.

## Vision
- 📡 Integrate GNSS, IMU, motion, and powertrain signals.
- 🔋 Extend to energy and environmental metrics (RFC-0004).
- 🧭 Support simulated (RS3) and industrial fleet data sources.
- 🌍 Enable contextual enrichment (weather, road type, safety, emissions).
- ⚖️ Separate **Core (open, MIT)** vs **Fleet Premium (proprietary KPIs)**.
- 🔬 Evolve through RFCs and open governance (RFC-0011).

## Quickstart
```bash
# Validate data against the v0.2 schema
ajv validate -s schemas/telemachus_core_v0.2.json -d examples/*.jsonl
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
- RFC-0001 – Core Schema
- RFC-0003 – Dataset Specification
- RFC-0004 – Extended FieldGroups
- RFC-0005 – Adapter Architecture
- RFC-0007 – Validation Framework
- RFC-0009 – RS3 Integration Pipeline
- RFC-0011 – Versioning & Governance

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